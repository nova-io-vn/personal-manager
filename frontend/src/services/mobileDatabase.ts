import { CapacitorSQLite, SQLiteConnection, type SQLiteDBConnection } from '@capacitor-community/sqlite'

const databaseName = 'personal_manager_local'
const sqlite = new SQLiteConnection(CapacitorSQLite)
let connection: SQLiteDBConnection | null = null
let opening: Promise<SQLiteDBConnection> | null = null

const schema = [
  `CREATE TABLE IF NOT EXISTS schedule_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, color TEXT NOT NULL, created_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, start_datetime TEXT NOT NULL, end_datetime TEXT NOT NULL, category_id INTEGER, color TEXT, reminder_minutes INTEGER NOT NULL DEFAULT 0, repeat_type TEXT NOT NULL DEFAULT 'NONE', repeat_until TEXT, completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(category_id) REFERENCES schedule_categories(id))`,
  `CREATE TABLE IF NOT EXISTS schedule_occurrence_states (id INTEGER PRIMARY KEY AUTOINCREMENT, schedule_id INTEGER NOT NULL, occurrence_start TEXT NOT NULL, completed INTEGER NOT NULL, completed_at TEXT, updated_at TEXT NOT NULL, UNIQUE(schedule_id, occurrence_start), FOREIGN KEY(schedule_id) REFERENCES schedules(id) ON DELETE CASCADE)`,
  `CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, initial_balance TEXT NOT NULL, current_balance TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS transaction_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, type TEXT NOT NULL, icon TEXT, color TEXT, created_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, category_id INTEGER, related_account_id INTEGER, type TEXT NOT NULL, amount TEXT NOT NULL, description TEXT, transaction_date TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'MANUAL', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(account_id) REFERENCES accounts(id), FOREIGN KEY(related_account_id) REFERENCES accounts(id), FOREIGN KEY(category_id) REFERENCES transaction_categories(id))`,
  `CREATE TABLE IF NOT EXISTS budgets (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER NOT NULL, amount TEXT NOT NULL, period TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(category_id) REFERENCES transaction_categories(id))`,
  `CREATE TABLE IF NOT EXISTS body_profiles (id INTEGER PRIMARY KEY CHECK(id = 1), height_cm TEXT NOT NULL, weight_kg TEXT NOT NULL, age INTEGER NOT NULL, sex TEXT NOT NULL, activity_level TEXT NOT NULL, goal TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS body_measurements (id INTEGER PRIMARY KEY AUTOINCREMENT, weight_kg TEXT NOT NULL, waist_cm TEXT, note TEXT, recorded_at TEXT NOT NULL, created_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS health_daily_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL UNIQUE, sleep_hours TEXT, water_ml INTEGER, steps INTEGER, exercise_type TEXT, exercise_minutes INTEGER, note TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS foods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, serving_quantity TEXT NOT NULL, serving_unit TEXT NOT NULL, calories TEXT NOT NULL, protein TEXT NOT NULL, carbs TEXT NOT NULL, fat TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS food_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, food_id INTEGER NOT NULL, quantity TEXT NOT NULL, meal_type TEXT NOT NULL, logged_date TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(food_id) REFERENCES foods(id))`,
  `CREATE TABLE IF NOT EXISTS journal_tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_date TEXT NOT NULL UNIQUE, mood TEXT NOT NULL, content TEXT NOT NULL, drawing_data TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS journal_entry_tags (entry_id INTEGER NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY(entry_id, tag_id), FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE, FOREIGN KEY(tag_id) REFERENCES journal_tags(id) ON DELETE CASCADE)`,
  `CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, channel TEXT NOT NULL DEFAULT 'LOCAL', title TEXT NOT NULL, message TEXT NOT NULL, scheduled_for TEXT NOT NULL, sent_at TEXT, status TEXT NOT NULL DEFAULT 'SENT', related_entity_type TEXT, related_entity_id INTEGER, read_at TEXT, created_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, note TEXT, due_date TEXT, completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY AUTOINCREMENT, person TEXT NOT NULL, direction TEXT NOT NULL, amount TEXT NOT NULL, paid_amount TEXT NOT NULL DEFAULT '0.00', due_date TEXT, note TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
]

const scheduleCategories = [
  ['Học tập', '#7898d4'], ['Công việc', '#7898d4'], ['Thể thao', '#74a98a'],
  ['Cá nhân', '#a38ac5'], ['Quan trọng', '#cf8a82'], ['Ăn uống', '#d5a765'],
]
const transactionCategories = [
  ['Food', 'EXPENSE', 'Utensils', '#d5a765'], ['Transport', 'EXPENSE', 'Car', '#7898d4'],
  ['Shopping', 'EXPENSE', 'ShoppingBag', '#a38ac5'], ['Entertainment', 'EXPENSE', 'Clapperboard', '#cf8a82'],
  ['Health', 'EXPENSE', 'HeartPulse', '#74a98a'], ['Education', 'EXPENSE', 'BookOpen', '#7898d4'],
  ['Bills', 'EXPENSE', 'Receipt', '#8793a5'], ['Other', 'EXPENSE', 'CircleEllipsis', '#8793a5'],
  ['Salary', 'INCOME', 'BriefcaseBusiness', '#74a98a'], ['Bonus', 'INCOME', 'Gift', '#74a98a'],
  ['Freelance', 'INCOME', 'Laptop', '#7898d4'], ['Investment', 'INCOME', 'ChartNoAxesCombined', '#7898d4'],
  ['Other Income', 'INCOME', 'CircleEllipsis', '#8793a5'],
]
export const defaultSettings: Record<string, string> = {
  currency: 'VND', default_reminder_minutes: '15', notifications_enabled: 'false',
  schedule_reminders_enabled: 'false', budget_warnings_enabled: 'false', journal_reminder_enabled: 'false',
  journal_reminder_time: '21:30', health_reminder_enabled: 'false', health_reminder_time: '20:00',
  daily_summary_enabled: 'false', daily_summary_time: '22:00', telegram_enabled: 'false',
  telegram_chat_id: '', gemini_enabled: 'false', gemini_model: 'gemini-2.5-flash',
}

function nowIso() { return new Date().toISOString() }

export async function openMobileDatabase(): Promise<SQLiteDBConnection> {
  if (connection) return connection
  if (!opening) opening = (async () => {
    await sqlite.checkConnectionsConsistency()
    const existing = await sqlite.isConnection(databaseName, false)
    const db = existing.result
      ? await sqlite.retrieveConnection(databaseName, false)
      : await sqlite.createConnection(databaseName, false, 'no-encryption', 1, false)
    if (!(await db.isDBOpen()).result) await db.open()
    await db.execute('PRAGMA foreign_keys = ON')
    for (const statement of schema) await db.execute(statement)
    try { await db.execute('ALTER TABLE journal_entries ADD COLUMN drawing_data TEXT') } catch { /* Existing tablet DB already has it. */ }
    const createdAt = nowIso()
    for (const [name, color] of scheduleCategories) await db.run('INSERT OR IGNORE INTO schedule_categories(name,color,created_at) VALUES(?,?,?)', [name, color, createdAt])
    for (const [name, type, icon, color] of transactionCategories) await db.run('INSERT OR IGNORE INTO transaction_categories(name,type,icon,color,created_at) VALUES(?,?,?,?,?)', [name, type, icon, color, createdAt])
    for (const [key, value] of Object.entries(defaultSettings)) await db.run('INSERT OR IGNORE INTO app_settings(key,value) VALUES(?,?)', [key, value])
    connection = db
    return db
  })()
  try { return await opening } finally { opening = null }
}

export async function dbQuery<T extends Record<string, unknown>>(sql: string, values: (string | number | null)[] = []): Promise<T[]> {
  const db = await openMobileDatabase()
  const result = await db.query(sql, values)
  return (result.values ?? []) as T[]
}

export async function dbRun(sql: string, values: (string | number | null)[] = []): Promise<number> {
  const db = await openMobileDatabase()
  const result = await db.run(sql, values, true, 'no')
  return Number(result.changes?.lastId ?? result.changes?.changes ?? 0)
}

export async function dbNow() { return nowIso() }
