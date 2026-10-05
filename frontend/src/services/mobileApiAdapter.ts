import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { AxiosError } from 'axios'
import { dbNow, dbQuery, dbRun, defaultSettings, openMobileDatabase } from './mobileDatabase'

type Value = string | number | boolean | null | undefined
type Row = Record<string, unknown>
type Params = Record<string, Value>

class LocalApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

const fail = (status: number, message: string): never => { throw new LocalApiError(status, message) }
const text = (value: unknown) => value == null ? null : String(value)
const yesNo = (value: unknown) => value ? 1 : 0
const bool = (value: unknown) => Number(value) !== 0
const decimalCents = (value: unknown) => {
  const match = /^(-?)(\d+)(?:\.(\d*))?$/.exec(String(value ?? '0'))
  if (!match) return 0n
  const cents = BigInt(match[2]) * 100n + BigInt(((match[3] ?? '') + '00').slice(0, 2))
  return match[1] ? -cents : cents
}
const moneyText = (cents: bigint) => `${cents < 0n ? '-' : ''}${String(cents < 0n ? -cents : cents).padStart(3, '0').slice(0, -2)}.${String(cents < 0n ? -cents : cents).padStart(3, '0').slice(-2)}`
const dateOnly = (value: string | null | undefined) => value ? value.slice(0, 10) : ''
const jsonData = (config: InternalAxiosRequestConfig) => {
  if (typeof config.data !== 'string') return (config.data ?? {}) as Row
  try { return JSON.parse(config.data) as Row } catch { return {} }
}

function expandedDate(base: Date, type: string, index: number): Date {
  if (type === 'DAILY') { const out = new Date(base); out.setDate(out.getDate() + index); return out }
  if (type === 'WEEKLY') { const out = new Date(base); out.setDate(out.getDate() + index * 7); return out }
  if (type === 'MONTHLY') {
    const out = new Date(base)
    const month = base.getMonth() + index
    out.setDate(1); out.setMonth(month)
    const lastDay = new Date(out.getFullYear(), out.getMonth() + 1, 0).getDate()
    out.setDate(Math.min(base.getDate(), lastDay))
    out.setHours(base.getHours(), base.getMinutes(), base.getSeconds(), base.getMilliseconds())
    return out
  }
  return new Date(base)
}

function occurrenceRows(schedule: Row, rangeStart: string, rangeEnd: string): Row[] {
  const baseStart = new Date(String(schedule.start_datetime))
  const baseEnd = new Date(String(schedule.end_datetime))
  const from = new Date(rangeStart).getTime(); const until = new Date(rangeEnd).getTime()
  const cutoff = schedule.repeat_until ? new Date(String(schedule.repeat_until)).getTime() : Number.POSITIVE_INFINITY
  const duration = baseEnd.getTime() - baseStart.getTime()
  const type = String(schedule.repeat_type ?? 'NONE')
  const occurrences: Row[] = []
  for (let index = 0; index < 5000; index += 1) {
    const start = expandedDate(baseStart, type, index)
    const epoch = start.getTime()
    if (epoch > cutoff || epoch >= until) break
    const end = new Date(epoch + duration)
    if (end.getTime() > from) occurrences.push({ ...schedule, start_datetime: start.toISOString(), end_datetime: end.toISOString(), series_start_datetime: schedule.start_datetime, is_recurring_occurrence: epoch !== baseStart.getTime() })
    if (type === 'NONE') break
  }
  return occurrences
}

async function objectById(table: string, id: number): Promise<Row> {
  const rows = await dbQuery<Row>(`SELECT * FROM ${table} WHERE id = ?`, [id])
  if (!rows[0]) fail(404, `${table} not found`)
  return rows[0]
}

async function accountsWithBalances(accounts: Row[]): Promise<Row[]> {
  const transactions = await dbQuery<Row>('SELECT account_id,related_account_id,type,amount FROM transactions')
  return accounts.map((account) => {
    let balance = decimalCents(account.initial_balance)
    for (const item of transactions) {
      const amount = decimalCents(item.amount)
      if (Number(item.account_id) === Number(account.id)) balance += item.type === 'INCOME' ? amount : -amount
      if (item.type === 'TRANSFER' && Number(item.related_account_id) === Number(account.id)) balance += amount
    }
    return { ...account, current_balance: moneyText(balance) }
  })
}

async function accountWithBalance(id: number): Promise<Row> {
  const account = await objectById('accounts', id)
  return (await accountsWithBalances([account]))[0]
}

async function listFoodLogs(date: string, meal?: string): Promise<Row[]> {
  const conditions = ['l.logged_date = ?']; const values: (string | number | null)[] = [date]
  if (meal) { conditions.push('l.meal_type = ?'); values.push(meal) }
  const logs = await dbQuery<Row>(`SELECT l.*, f.name AS f_name, f.serving_quantity AS f_serving_quantity, f.serving_unit AS f_serving_unit, f.calories AS f_calories, f.protein AS f_protein, f.carbs AS f_carbs, f.fat AS f_fat, f.created_at AS f_created_at, f.updated_at AS f_updated_at FROM food_logs l JOIN foods f ON f.id=l.food_id WHERE ${conditions.join(' AND ')} ORDER BY l.id`, values)
  return logs.map((log) => ({ id: log.id, food_id: log.food_id, quantity: log.quantity, meal_type: log.meal_type, logged_date: log.logged_date, created_at: log.created_at, food: { id: log.food_id, name: log.f_name, serving_quantity: log.f_serving_quantity, serving_unit: log.f_serving_unit, calories: log.f_calories, protein: log.f_protein, carbs: log.f_carbs, fat: log.f_fat, created_at: log.f_created_at, updated_at: log.f_updated_at } }))
}

function scaleNutrient(value: unknown, quantity: unknown, serving: unknown) {
  const denominator = decimalCents(serving)
  if (denominator <= 0n) return '0.0'
  const numerator = decimalCents(value) * decimalCents(quantity)
  const cents = (numerator + denominator / 2n) / denominator
  return moneyText(cents)
}

async function nutrition(date: string): Promise<Row> {
  const logs = await listFoodLogs(date)
  const totals = { calories: 0n, protein: 0n, carbs: 0n, fat: 0n }
  const meals: Record<string, Row[]> = { BREAKFAST: [], LUNCH: [], DINNER: [], SNACK: [] }
  for (const log of logs) {
    const food = log.food as Row
    for (const key of Object.keys(totals) as Array<keyof typeof totals>) totals[key] += decimalCents(scaleNutrient(food[key], log.quantity, food.serving_quantity))
    meals[String(log.meal_type)].push(log)
  }
  return { date, ...Object.fromEntries(Object.entries(totals).map(([key, value]) => [key, moneyText(value)])), meals }
}

async function healthSummary(date: string) {
  const profile = (await dbQuery<Row>('SELECT * FROM body_profiles WHERE id=1'))[0] ?? null
  const measurements = await dbQuery<Row>('SELECT * FROM body_measurements ORDER BY recorded_at DESC,id DESC LIMIT 2')
  const weight = measurements[0]?.weight_kg ?? profile?.weight_kg ?? null
  const today = (await dbQuery<Row>('SELECT * FROM health_daily_logs WHERE date=?', [date]))[0] ?? null
  let metrics: Row | null = null
  if (profile && weight != null) {
    const height = Number(profile.height_cm); const mass = Number(weight)
    const bmi = mass / ((height / 100) ** 2)
    const bmr = 10 * mass + 6.25 * height - 5 * Number(profile.age) + (profile.sex === 'MALE' ? 5 : -161)
    const multiplier: Record<string, number> = { SEDENTARY: 1.2, LIGHT: 1.375, MODERATE: 1.55, ACTIVE: 1.725, VERY_ACTIVE: 1.9 }
    const tdee = bmr * multiplier[String(profile.activity_level)]
    const adjustment = profile.goal === 'LOSE_WEIGHT' ? -300 : profile.goal === 'GAIN_WEIGHT' ? 300 : 0
    const round = (value: number) => (Math.sign(value) * Math.round((Math.abs(value) + Number.EPSILON) * 10) / 10).toFixed(1)
    metrics = { bmi: round(bmi), bmr: round(bmr), tdee: round(tdee), target_calories: round(tdee + adjustment) }
  }
  const nutrients = await nutrition(date)
  return { profile, metrics, weight, weight_change: measurements.length > 1 ? (Number(measurements[0].weight_kg) - Number(measurements[1].weight_kg)).toFixed(1) : null, today, nutrition: { calories: nutrients.calories, protein: nutrients.protein, carbs: nutrients.carbs, fat: nutrients.fat } }
}

async function journalEntry(date: string): Promise<Row | null> {
  const entry = (await dbQuery<Row>('SELECT * FROM journal_entries WHERE entry_date=?', [date]))[0]
  if (!entry) return null
  const tags = await dbQuery<Row>('SELECT t.* FROM journal_tags t JOIN journal_entry_tags et ON et.tag_id=t.id WHERE et.entry_id=? ORDER BY t.name', [Number(entry.id)])
  return { ...entry, tags }
}

async function handle(method: string, pathname: string, query: URLSearchParams, input: Row): Promise<{ data: unknown; status: number }> {
  await openMobileDatabase()
  const segments = pathname.split('/').filter(Boolean).map(decodeURIComponent)
  const [root, idPart, action] = segments
  const id = Number(idPart)
  const get = (key: string) => query.get(key) ?? undefined
  const data = input
  const t = await dbNow()

  if (method === 'GET' && root === 'health' && !idPart) return { data: { status: 'ok', storage: 'device' }, status: 200 }
  if (root === 'schedule-categories') {
    if (method === 'GET') return { data: await dbQuery('SELECT * FROM schedule_categories ORDER BY name'), status: 200 }
    if (method === 'POST') {
      const newId = await dbRun('INSERT INTO schedule_categories(name,color,created_at) VALUES(?,?,?)', [String(data.name ?? '').trim(), String(data.color ?? '#7898d4'), t])
      return { data: await objectById('schedule_categories', newId), status: 201 }
    }
  }
  if (root === 'schedules') {
    if (method === 'GET') {
      if (idPart) return { data: await objectById('schedules', id), status: 200 }
      const all = await dbQuery<Row>('SELECT * FROM schedules ORDER BY start_datetime')
      const start = get('start'); const end = get('end')
      if (!start || !end) return { data: all.map((row) => ({ ...row, completed: bool(row.completed) })), status: 200 }
      if (new Date(end) <= new Date(start)) fail(422, 'end must be after start')
      const filtered: Row[] = []
      for (const schedule of all) {
        if (get('category_id') && Number(schedule.category_id) !== Number(get('category_id'))) continue
        const occurrences = occurrenceRows(schedule, start, end)
        for (const occurrence of occurrences) {
          const state = (await dbQuery<Row>('SELECT completed FROM schedule_occurrence_states WHERE schedule_id=? AND occurrence_start=?', [Number(schedule.id), String(occurrence.start_datetime)]))[0]
          occurrence.completed = state ? bool(state.completed) : bool(schedule.completed)
          if (get('completed') !== undefined && occurrence.completed !== (get('completed') === 'true')) continue
          filtered.push(occurrence)
        }
      }
      return { data: filtered.sort((a, b) => String(a.start_datetime).localeCompare(String(b.start_datetime))), status: 200 }
    }
    if (method === 'POST' && !idPart) {
      const start = String(data.start_datetime ?? ''); const end = String(data.end_datetime ?? '')
      if (!String(data.title ?? '').trim()) fail(422, 'title cannot be empty')
      if (new Date(end) <= new Date(start)) fail(422, 'end_datetime must be after start_datetime')
      const newId = await dbRun('INSERT INTO schedules(title,description,start_datetime,end_datetime,category_id,color,reminder_minutes,repeat_type,repeat_until,completed,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', [String(data.title).trim(), text(data.description), start, end, data.category_id == null ? null : Number(data.category_id), text(data.color), Number(data.reminder_minutes ?? 0), String(data.repeat_type ?? 'NONE'), text(data.repeat_until), yesNo(data.completed), t, t])
      return { data: await objectById('schedules', newId), status: 201 }
    }
    if (method === 'PATCH' && action === 'occurrence-completion') {
      const schedule = await objectById('schedules', id)
      const occurrenceStart = String(data.occurrence_start ?? '')
      const range = occurrenceRows(schedule, new Date(new Date(occurrenceStart).getTime() - 1).toISOString(), new Date(new Date(occurrenceStart).getTime() + 1).toISOString())
      const occurrence = range.find((row) => row.start_datetime === occurrenceStart)
      if (!occurrence) fail(422, 'occurrence_start is not a valid schedule occurrence')
      const done = yesNo(data.completed); const completedAt = done ? t : null
      await dbRun('INSERT INTO schedule_occurrence_states(schedule_id,occurrence_start,completed,completed_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(schedule_id,occurrence_start) DO UPDATE SET completed=excluded.completed,completed_at=excluded.completed_at,updated_at=excluded.updated_at', [id, occurrenceStart, done, completedAt, t])
      return { data: { ...occurrence, completed: Boolean(done) }, status: 200 }
    }
    if (method === 'PATCH' && idPart) {
      const current = await objectById('schedules', id)
      const fields = ['title', 'description', 'start_datetime', 'end_datetime', 'category_id', 'color', 'reminder_minutes', 'repeat_type', 'repeat_until', 'completed']
      const next = { ...current, ...Object.fromEntries(fields.filter((key) => key in data).map((key) => [key, data[key]])) }
      if (!String(next.title ?? '').trim()) fail(422, 'title cannot be empty')
      if (new Date(String(next.end_datetime)) <= new Date(String(next.start_datetime))) fail(422, 'end_datetime must be after start_datetime')
      const assignments = fields.filter((key) => key in data).map((key) => `${key}=?`)
      if (assignments.length) await dbRun(`UPDATE schedules SET ${assignments.join(',')},updated_at=? WHERE id=?`, [...fields.filter((key) => key in data).map((key) => key === 'completed' ? yesNo(data[key]) : data[key] == null ? null : data[key] as string | number), t, id])
      return { data: await objectById('schedules', id), status: 200 }
    }
    if (method === 'DELETE' && idPart) { await objectById('schedules', id); await dbRun('DELETE FROM schedules WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'accounts') {
    if (method === 'GET' && !idPart) return { data: await accountsWithBalances(await dbQuery('SELECT * FROM accounts ORDER BY id')), status: 200 }
    if (method === 'GET' && idPart) return { data: await accountWithBalance(id), status: 200 }
    if (method === 'POST') {
      const initial = moneyText(decimalCents(data.initial_balance ?? '0'))
      const newId = await dbRun('INSERT INTO accounts(name,type,initial_balance,current_balance,created_at,updated_at) VALUES(?,?,?,?,?,?)', [String(data.name ?? '').trim(), String(data.type), initial, initial, t, t])
      return { data: await accountWithBalance(newId), status: 201 }
    }
    if (method === 'PATCH' && idPart) {
      await objectById('accounts', id)
      const fields = ['name', 'type'].filter((key) => key in data)
      if (fields.length) await dbRun(`UPDATE accounts SET ${fields.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...fields.map((key) => data[key] as string), t, id])
      return { data: await accountWithBalance(id), status: 200 }
    }
    if (method === 'DELETE' && idPart) {
      await objectById('accounts', id)
      if ((await dbQuery('SELECT id FROM transactions WHERE account_id=? OR related_account_id=? LIMIT 1', [id, id])).length) fail(409, 'Cannot delete an account with transactions')
      await dbRun('DELETE FROM accounts WHERE id=?', [id]); return { data: null, status: 204 }
    }
  }
  if (root === 'transaction-categories' && method === 'GET') return { data: await dbQuery('SELECT * FROM transaction_categories ORDER BY type,name'), status: 200 }
  if (root === 'transactions') {
    if (method === 'GET' && !idPart) {
      const rows = await dbQuery<Row>('SELECT * FROM transactions ORDER BY transaction_date DESC,id DESC')
      return { data: rows.filter((row) => (!get('start_date') || String(row.transaction_date) >= String(get('start_date'))) && (!get('end_date') || String(row.transaction_date) <= String(get('end_date'))) && (!get('account_id') || Number(row.account_id) === Number(get('account_id')) || Number(row.related_account_id) === Number(get('account_id'))) && (!get('category_id') || Number(row.category_id) === Number(get('category_id'))) && (!get('type') || row.type === get('type'))), status: 200 }
    }
    if (method === 'GET' && idPart) return { data: await objectById('transactions', id), status: 200 }
    if (method === 'POST' || (method === 'PATCH' && idPart)) {
      const current = idPart ? await objectById('transactions', id) : null
      const next = { ...(current ?? {}), ...data }
      const type = String(next.type); const amount = decimalCents(next.amount)
      if (amount <= 0n) fail(400, 'Transaction amount must be greater than zero')
      if (type === 'TRANSFER') {
        if (!next.related_account_id || Number(next.related_account_id) === Number(next.account_id) || next.category_id != null) fail(400, 'Transfers require two different accounts')
        await objectById('accounts', Number(next.related_account_id))
      } else {
        if (next.related_account_id != null) fail(400, 'related_account_id is only valid for transfers')
        const category = await objectById('transaction_categories', Number(next.category_id))
        if (category.type !== type) fail(400, `category type must be ${type}`)
      }
      await objectById('accounts', Number(next.account_id))
      let resultId = id
      if (current) {
        const fields = ['account_id', 'category_id', 'related_account_id', 'type', 'amount', 'description', 'transaction_date', 'source']
        const filtered = fields.filter((key) => key in next)
        await dbRun(`UPDATE transactions SET ${filtered.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...filtered.map((key) => key === 'amount' ? moneyText(decimalCents(next[key])) : next[key] == null ? null : next[key] as string | number), t, id])
      } else {
        resultId = await dbRun('INSERT INTO transactions(account_id,category_id,related_account_id,type,amount,description,transaction_date,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)', [Number(next.account_id), next.category_id == null ? null : Number(next.category_id), next.related_account_id == null ? null : Number(next.related_account_id), type, moneyText(amount), text(next.description), String(next.transaction_date), String(next.source ?? 'MANUAL'), t, t])
      }
      return { data: await objectById('transactions', resultId), status: current ? 200 : 201 }
    }
    if (method === 'DELETE' && idPart) { await objectById('transactions', id); await dbRun('DELETE FROM transactions WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'budgets') {
    if (method === 'GET') return { data: await dbQuery('SELECT * FROM budgets ORDER BY start_date DESC,id DESC'), status: 200 }
    if (method === 'POST' || (method === 'PATCH' && idPart)) {
      const current = idPart ? await objectById('budgets', id) : null
      const next = { ...(current ?? {}), ...data }
      const category = await objectById('transaction_categories', Number(next.category_id))
      if (category.type !== 'EXPENSE') fail(400, 'Budgets must use expense categories')
      if (String(next.end_date) < String(next.start_date)) fail(422, 'end_date must be on or after start_date')
      let resultId = id
      if (current) {
        const fields = ['category_id', 'amount', 'period', 'start_date', 'end_date'].filter((key) => key in data)
        await dbRun(`UPDATE budgets SET ${fields.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...fields.map((key) => key === 'amount' ? moneyText(decimalCents(next[key])) : next[key] as string | number), t, id])
      } else resultId = await dbRun('INSERT INTO budgets(category_id,amount,period,start_date,end_date,created_at,updated_at) VALUES(?,?,?,?,?,?,?)', [Number(next.category_id), moneyText(decimalCents(next.amount)), String(next.period), String(next.start_date), String(next.end_date), t, t])
      return { data: await objectById('budgets', resultId), status: current ? 200 : 201 }
    }
    if (method === 'DELETE' && idPart) { await objectById('budgets', id); await dbRun('DELETE FROM budgets WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'health') {
    if (idPart === 'profile' && method === 'GET') {
      const profile = (await dbQuery<Row>('SELECT * FROM body_profiles WHERE id=1'))[0]
      if (!profile) fail(404, 'Body profile not found')
      return { data: profile, status: 200 }
    }
    if (idPart === 'profile' && method === 'PUT') {
      const current = (await dbQuery<Row>('SELECT * FROM body_profiles WHERE id=1'))[0]
      if (current) await dbRun('UPDATE body_profiles SET height_cm=?,weight_kg=?,age=?,sex=?,activity_level=?,goal=?,updated_at=? WHERE id=1', [String(data.height_cm), String(data.weight_kg), Number(data.age), String(data.sex), String(data.activity_level), String(data.goal), t])
      else await dbRun('INSERT INTO body_profiles(id,height_cm,weight_kg,age,sex,activity_level,goal,created_at,updated_at) VALUES(1,?,?,?,?,?,?,?,?)', [String(data.height_cm), String(data.weight_kg), Number(data.age), String(data.sex), String(data.activity_level), String(data.goal), t, t])
      return { data: (await dbQuery<Row>('SELECT * FROM body_profiles WHERE id=1'))[0], status: 200 }
    }
    if (idPart === 'summary' && method === 'GET') return { data: await healthSummary(get('date') ?? dateOnly(t)), status: 200 }
    if (idPart === 'measurements') {
      if (method === 'GET') {
        const rows = await dbQuery<Row>('SELECT * FROM body_measurements ORDER BY recorded_at DESC,id DESC')
        return { data: rows.filter((row) => (!get('start') || String(row.recorded_at) >= String(get('start'))) && (!get('end') || String(row.recorded_at) <= String(get('end')))), status: 200 }
      }
      if (method === 'POST' || (method === 'PATCH' && action)) {
        const current = action ? await objectById('body_measurements', Number(action)) : null
        const next = { ...(current ?? {}), ...data }
        if (current) {
          const fields = ['weight_kg', 'waist_cm', 'note', 'recorded_at'].filter((key) => key in data)
          await dbRun(`UPDATE body_measurements SET ${fields.map((key) => `${key}=?`).join(',')} WHERE id=?`, [...fields.map((key) => next[key] == null ? null : String(next[key])), Number(action)])
          return { data: await objectById('body_measurements', Number(action)), status: 200 }
        }
        const newId = await dbRun('INSERT INTO body_measurements(weight_kg,waist_cm,note,recorded_at,created_at) VALUES(?,?,?,?,?)', [String(next.weight_kg), text(next.waist_cm), text(next.note), String(next.recorded_at), t])
        return { data: await objectById('body_measurements', newId), status: 201 }
      }
      if (method === 'DELETE' && action) { await objectById('body_measurements', Number(action)); await dbRun('DELETE FROM body_measurements WHERE id=?', [Number(action)]); return { data: null, status: 204 } }
    }
    if (idPart === 'daily') {
      const date = action ?? ''
      if (method === 'GET') {
        const rows = await dbQuery<Row>('SELECT * FROM health_daily_logs ORDER BY date DESC')
        return { data: rows.filter((row) => (!get('start') || String(row.date) >= String(get('start'))) && (!get('end') || String(row.date) <= String(get('end')))), status: 200 }
      }
      if (method === 'PUT') {
        const existing = (await dbQuery<Row>('SELECT id FROM health_daily_logs WHERE date=?', [date]))[0]
        if (existing) await dbRun('UPDATE health_daily_logs SET sleep_hours=?,water_ml=?,steps=?,exercise_type=?,exercise_minutes=?,note=?,updated_at=? WHERE date=?', [text(data.sleep_hours), data.water_ml == null ? null : Number(data.water_ml), data.steps == null ? null : Number(data.steps), text(data.exercise_type), data.exercise_minutes == null ? null : Number(data.exercise_minutes), text(data.note), t, date])
        else await dbRun('INSERT INTO health_daily_logs(date,sleep_hours,water_ml,steps,exercise_type,exercise_minutes,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)', [date, text(data.sleep_hours), data.water_ml == null ? null : Number(data.water_ml), data.steps == null ? null : Number(data.steps), text(data.exercise_type), data.exercise_minutes == null ? null : Number(data.exercise_minutes), text(data.note), t, t])
        return { data: (await dbQuery<Row>('SELECT * FROM health_daily_logs WHERE date=?', [date]))[0], status: 200 }
      }
    }
  }
  if (root === 'foods') {
    if (method === 'GET' && !idPart) {
      const rows = await dbQuery<Row>('SELECT * FROM foods ORDER BY name COLLATE NOCASE')
      const search = (get('search') ?? '').toLocaleLowerCase()
      return { data: search ? rows.filter((row) => String(row.name).toLocaleLowerCase().includes(search)) : rows, status: 200 }
    }
    if (method === 'GET' && idPart) return { data: await objectById('foods', id), status: 200 }
    if (method === 'POST' || (method === 'PATCH' && idPart)) {
      const current = idPart ? await objectById('foods', id) : null; const next = { ...(current ?? {}), ...data }
      let resultId = id
      const fields = ['name', 'serving_quantity', 'serving_unit', 'calories', 'protein', 'carbs', 'fat']
      if (current) {
        const modified = fields.filter((key) => key in data)
        await dbRun(`UPDATE foods SET ${modified.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...modified.map((key) => String(next[key])), t, id])
      } else resultId = await dbRun('INSERT INTO foods(name,serving_quantity,serving_unit,calories,protein,carbs,fat,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)', [String(next.name).trim(), String(next.serving_quantity), String(next.serving_unit), String(next.calories), String(next.protein ?? '0'), String(next.carbs ?? '0'), String(next.fat ?? '0'), t, t])
      return { data: await objectById('foods', resultId), status: current ? 200 : 201 }
    }
    if (method === 'DELETE' && idPart) {
      await objectById('foods', id)
      if ((await dbQuery('SELECT id FROM food_logs WHERE food_id=? LIMIT 1', [id])).length) fail(409, 'Cannot delete a food with logs')
      await dbRun('DELETE FROM foods WHERE id=?', [id]); return { data: null, status: 204 }
    }
  }
  if (root === 'food-logs') {
    if (method === 'GET') return { data: await listFoodLogs(get('logged_date') ?? dateOnly(t), get('meal_type')), status: 200 }
    if (method === 'POST' || (method === 'PATCH' && idPart)) {
      const current = idPart ? await objectById('food_logs', id) : null; const next = { ...(current ?? {}), ...data }
      if (decimalCents(next.quantity) <= 0n) fail(422, 'quantity must be greater than zero')
      await objectById('foods', Number(next.food_id))
      let resultId = id
      if (current) {
        const fields = ['food_id', 'quantity', 'meal_type', 'logged_date'].filter((key) => key in data)
        await dbRun(`UPDATE food_logs SET ${fields.map((key) => `${key}=?`).join(',')} WHERE id=?`, [...fields.map((key) => next[key] as string | number), id])
      } else resultId = await dbRun('INSERT INTO food_logs(food_id,quantity,meal_type,logged_date,created_at) VALUES(?,?,?,?,?)', [Number(next.food_id), String(next.quantity), String(next.meal_type), String(next.logged_date), t])
      return { data: (await listFoodLogs(String(next.logged_date))).find((row) => Number(row.id) === resultId), status: current ? 200 : 201 }
    }
    if (method === 'DELETE' && idPart) { await objectById('food_logs', id); await dbRun('DELETE FROM food_logs WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'nutrition' && idPart === 'summary' && method === 'GET') return { data: await nutrition(get('date') ?? dateOnly(t)), status: 200 }
  if (root === 'tasks') {
    if (method === 'GET' && !idPart) {
      const rows = await dbQuery<Row>('SELECT * FROM tasks ORDER BY completed ASC, due_date IS NULL, due_date ASC, created_at DESC')
      return { data: rows.map((row) => ({ ...row, completed: bool(row.completed) })).filter((row) => get('include_completed') !== 'false' || !row.completed), status: 200 }
    }
    if (method === 'POST') { const title = String(data.title ?? '').trim(); if (!title) fail(422, 'title cannot be empty'); const newId = await dbRun('INSERT INTO tasks(title,note,due_date,completed,created_at,updated_at) VALUES(?,?,?,?,?,?)', [title, text(data.note), text(data.due_date), 0, t, t]); return { data: await objectById('tasks', newId), status: 201 } }
    if (method === 'PATCH' && idPart) { const current = await objectById('tasks', id); const fields = ['title', 'note', 'due_date', 'completed'].filter((key) => key in data); if (fields.includes('title') && !String(data.title ?? '').trim()) fail(422, 'title cannot be empty'); if (fields.length) await dbRun(`UPDATE tasks SET ${fields.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...fields.map((key) => key === 'completed' ? yesNo(data[key]) : text(data[key])), t, id]); return { data: { ...current, ...data, completed: 'completed' in data ? Boolean(data.completed) : bool(current.completed), updated_at: t }, status: 200 } }
    if (method === 'DELETE' && idPart) { await objectById('tasks', id); await dbRun('DELETE FROM tasks WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'debts') {
    if (method === 'GET') return { data: await dbQuery('SELECT * FROM debts ORDER BY due_date IS NULL, due_date ASC, created_at DESC'), status: 200 }
    if (method === 'POST') { const amount = decimalCents(data.amount); const paid = decimalCents(data.paid_amount ?? '0'); if (amount <= 0n || paid < 0n || paid > amount) fail(422, 'Invalid debt amount'); const newId = await dbRun('INSERT INTO debts(person,direction,amount,paid_amount,due_date,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)', [String(data.person ?? '').trim(), String(data.direction), String(data.amount), String(data.paid_amount ?? '0'), text(data.due_date), text(data.note), t, t]); return { data: await objectById('debts', newId), status: 201 } }
    if (method === 'PATCH' && idPart) { const current = await objectById('debts', id); const next = { ...current, ...data }; if (decimalCents(next.amount) <= 0n || decimalCents(next.paid_amount ?? '0') > decimalCents(next.amount)) fail(422, 'Invalid debt amount'); const fields = ['person', 'direction', 'amount', 'paid_amount', 'due_date', 'note'].filter((key) => key in data); if (fields.length) await dbRun(`UPDATE debts SET ${fields.map((key) => `${key}=?`).join(',')},updated_at=? WHERE id=?`, [...fields.map((key) => text(data[key])), t, id]); return { data: { ...current, ...data, updated_at: t }, status: 200 } }
    if (method === 'DELETE' && idPart) { await objectById('debts', id); await dbRun('DELETE FROM debts WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'journals') {
    if (method === 'GET' && !idPart) {
      const entries = await dbQuery<Row>('SELECT * FROM journal_entries ORDER BY entry_date DESC')
      const filtered = entries.filter((entry) => (!get('start_date') || String(entry.entry_date) >= String(get('start_date'))) && (!get('end_date') || String(entry.entry_date) <= String(get('end_date'))) && (!get('mood') || entry.mood === get('mood')))
      const result = await Promise.all(filtered.map((entry) => journalEntry(String(entry.entry_date))))
      return { data: result.filter((entry) => !get('tag') || (entry?.tags as Row[]).some((tag) => tag.name === get('tag'))), status: 200 }
    }
    if (method === 'GET' && idPart) { const entry = await journalEntry(idPart); if (!entry) fail(404, 'Journal entry not found'); return { data: entry, status: 200 } }
    if (method === 'PUT' && idPart) {
      const current = (await dbQuery<Row>('SELECT * FROM journal_entries WHERE entry_date=?', [idPart]))[0]
      let entryId: number
      if (current) { entryId = Number(current.id); await dbRun('UPDATE journal_entries SET mood=?,content=?,drawing_data=?,updated_at=? WHERE id=?', [String(data.mood), String(data.content ?? ''), text(data.drawing_data), t, entryId]); await dbRun('DELETE FROM journal_entry_tags WHERE entry_id=?', [entryId]) }
      else entryId = await dbRun('INSERT INTO journal_entries(entry_date,mood,content,drawing_data,created_at,updated_at) VALUES(?,?,?,?,?,?)', [idPart, String(data.mood), String(data.content ?? ''), text(data.drawing_data), t, t])
      for (const tagId of Array.isArray(data.tag_ids) ? data.tag_ids : []) {
        await objectById('journal_tags', Number(tagId))
        await dbRun('INSERT OR IGNORE INTO journal_entry_tags(entry_id,tag_id) VALUES(?,?)', [entryId, Number(tagId)])
      }
      return { data: await journalEntry(idPart), status: 200 }
    }
    if (method === 'DELETE' && idPart) { const current = await journalEntry(idPart); if (!current) fail(404, 'Journal entry not found'); await dbRun('DELETE FROM journal_entries WHERE entry_date=?', [idPart]); return { data: null, status: 204 } }
  }
  if (root === 'journal-tags') {
    if (method === 'GET') return { data: await dbQuery('SELECT * FROM journal_tags ORDER BY name'), status: 200 }
    if (method === 'POST') {
      const name = String(data.name ?? '').trim(); if (!name) fail(422, 'Tag name cannot be empty')
      try { const newId = await dbRun('INSERT INTO journal_tags(name,created_at) VALUES(?,?)', [name, t]); return { data: await objectById('journal_tags', newId), status: 201 } }
      catch { fail(409, 'Journal tag already exists') }
    }
  }
  if (root === 'settings') {
    if (method === 'GET') {
      const saved = await dbQuery<Row>('SELECT key,value FROM app_settings')
      const values = Object.fromEntries(saved.map((row) => [String(row.key), String(row.value)]))
      return { data: { ...Object.fromEntries(Object.entries({ ...defaultSettings, ...values }).map(([key, value]) => [key, key.endsWith('_enabled') ? value === 'true' : key === 'default_reminder_minutes' ? Number(value) : value])), telegram_bot_token: null, telegram_token_configured: false, gemini_api_key: null, gemini_key_configured: false, telegram_chat_id: values.telegram_chat_id || null }, status: 200 }
    }
    if (method === 'PATCH') {
      if (data.telegram_bot_token || data.gemini_api_key) fail(400, 'Telegram and Gemini credentials are unavailable in offline tablet mode')
      for (const [key, value] of Object.entries(data)) {
        if (key === 'telegram_bot_token' || key === 'gemini_api_key') continue
        if (!(key in defaultSettings)) continue
        await dbRun('INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', [key, String(value ?? '')])
      }
      return handle('GET', '/settings', new URLSearchParams(), {})
    }
    if (method === 'POST' && (idPart === 'telegram' || idPart === 'gemini')) fail(503, 'Integration requires an internet-connected service and credentials')
  }
  if (root === 'notifications') {
    if (method === 'GET') {
      const limit = Math.max(1, Math.min(100, Number(get('limit') ?? 30)))
      const rows = await dbQuery<Row>('SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?', [limit])
      return { data: get('unread_only') === 'true' ? rows.filter((row) => !row.read_at) : rows, status: 200 }
    }
    if (method === 'PATCH' && action === 'read') { await objectById('notifications', id); await dbRun('UPDATE notifications SET read_at=? WHERE id=?', [t, id]); return { data: await objectById('notifications', id), status: 200 } }
    if (method === 'DELETE' && idPart) { await objectById('notifications', id); await dbRun('DELETE FROM notifications WHERE id=?', [id]); return { data: null, status: 204 } }
  }
  if (root === 'data' && idPart === 'backups' && action === 'latest' && method === 'GET') return { data: null, status: 200 }
  if (root === 'data') fail(501, 'Sao lưu/khôi phục trên tablet chưa được hỗ trợ trong bản này')
  if (root === 'ai') fail(503, 'Gemini is unavailable in offline tablet mode')
  return fail(404, 'Not found')
}

export const mobileApiAdapter: AxiosAdapter = async (config) => {
  const route = config.url ?? '/'
  const path = route.split('?')[0]
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries((config.params ?? {}) as Params)) if (value != null) params.set(key, String(value))
  try {
    const result = await handle((config.method ?? 'get').toUpperCase(), path, params, jsonData(config))
    const response: AxiosResponse = { data: result.data, status: result.status, statusText: result.status === 204 ? 'No Content' : 'OK', headers: {}, config, request: null }
    if (result.status >= 400) throw new AxiosError(`Request failed with status code ${result.status}`, undefined, config, null, response)
    return response
  } catch (error) {
    if (error instanceof AxiosError) throw error
    const status = error instanceof LocalApiError ? error.status : 500
    const message = error instanceof Error ? error.message : 'Local data request failed'
    const response: AxiosResponse = { data: { detail: message }, status, statusText: 'Error', headers: {}, config, request: null }
    throw new AxiosError(message, undefined, config, null, response)
  }
}
