import assert from 'node:assert/strict'
import { chromium } from '@playwright/test'

const mode = process.argv[2] ?? 'seed'
const debugPort = process.argv[3] ?? '9222'
if (process.argv[4] !== '--isolated-test-data') {
  throw new Error('Refusing to modify application data without --isolated-test-data; launch the installer with a temporary --user-data-dir first.')
}
const browser = await chromium.connectOverCDP(`http://127.0.0.1:${debugPort}`)
try {
  const pages = browser.contexts().flatMap((context) => context.pages())
  const page = pages.find((candidate) => candidate.url().startsWith('file:'))
  assert.ok(page, 'Electron renderer page is available')
  await page.waitForLoadState('domcontentloaded')
  process.stdout.write(JSON.stringify({ url: page.url(), title: await page.title(), body: (await page.locator('body').innerText()).slice(0, 500), bridge: await page.evaluate(() => Boolean(window.personalManager)) }) + '\n')
  const result = await page.evaluate(async (currentMode) => {
    const api = window.personalManager?.apiBaseUrl
    if (!api) throw new Error('Electron preload did not provide the local API URL')
    const call = async (path, method = 'GET', body) => {
      const response = await fetch(`${api}${path}`, {
        method,
        headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
      })
      const contentType = response.headers.get('content-type') ?? ''
      const value = contentType.includes('application/json') ? await response.json() : await response.text()
      if (!response.ok) throw new Error(`${method} ${path}: ${response.status} ${JSON.stringify(value)}`)
      return value
    }
    const health = await call('/health')
    if (health.status !== 'ok') throw new Error('Packaged API health check failed')
    if (currentMode === 'verify') {
      const accounts = await call('/accounts')
      const journal = await call(`/journals/${new Date().toISOString().slice(0, 10)}`)
      const settings = await call('/settings')
      return { health: health.status, account: accounts.find((item) => item.name === 'Release smoke')?.name, journal: journal.content, currency: settings.currency }
    }

    const account = await call('/accounts', 'POST', { name: 'Release smoke', type: 'CASH', initial_balance: '1000' })
    const categories = await call('/transaction-categories')
    const expense = categories.find((item) => item.type === 'EXPENSE')
    await call('/transactions', 'POST', { account_id: account.id, category_id: expense.id, type: 'EXPENSE', amount: '25', transaction_date: new Date().toISOString().slice(0, 10), description: 'Packaged smoke' })
    const balance = (await call(`/accounts/${account.id}`)).current_balance

    const category = (await call('/schedule-categories'))[0]
    const start = new Date(Date.now() + 24 * 60 * 60 * 1000)
    start.setMinutes(0, 0, 0)
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    await call('/schedules', 'POST', { title: 'Release smoke schedule', start_datetime: start.toISOString(), end_datetime: end.toISOString(), category_id: category.id, reminder_minutes: 0, repeat_type: 'NONE', completed: false })

    await call('/health/profile', 'PUT', { height_cm: '172', weight_kg: '68', age: 30, sex: 'MALE', activity_level: 'MODERATE', goal: 'MAINTAIN' })
    const today = new Date().toISOString().slice(0, 10)
    await call(`/health/daily/${today}`, 'PUT', { sleep_hours: '7.5', water_ml: 1800, steps: 5000, exercise_minutes: 20 })
    const food = await call('/foods', 'POST', { name: 'Release smoke food', serving_quantity: '100', serving_unit: 'g', calories: '200', protein: '10', carbs: '20', fat: '5' })
    await call('/food-logs', 'POST', { food_id: food.id, quantity: '150', meal_type: 'LUNCH', logged_date: today })
    const nutrition = await call(`/nutrition/summary?date=${today}`)
    await call(`/journals/${today}`, 'PUT', { mood: 'GOOD', content: 'Packaged restart persistence check', tag_ids: [] })
    await call('/settings', 'PATCH', { currency: 'USD' })
    const notifications = await call('/notifications')

    const backupResponse = await fetch(`${api}/data/backup`, { method: 'POST' })
    if (!backupResponse.ok) throw new Error(`Backup creation failed: ${backupResponse.status}`)
    const backup = await backupResponse.blob()
    await call('/accounts', 'POST', { name: 'Should be restored away', type: 'CASH', initial_balance: '1' })
    const form = new FormData()
    form.append('file', backup, 'smoke.zip')
    const restoreResponse = await fetch(`${api}/data/restore`, { method: 'POST', body: form })
    const restore = await restoreResponse.json()
    if (!restoreResponse.ok || !restore.success) throw new Error('Backup restore smoke failed')
    const accountsAfterRestore = await call('/accounts')
    return {
      health: health.status,
      accountBalance: balance,
      scheduleCount: (await call('/schedules')).length,
      bmi: (await call('/health/summary')).metrics?.bmi,
      calories: nutrition.calories,
      notifications: notifications.length,
      restoredAccount: accountsAfterRestore.some((item) => item.name === 'Release smoke'),
      discardedPostBackupAccount: accountsAfterRestore.some((item) => item.name === 'Should be restored away'),
      safetyBackup: restore.safety_backup,
      restartRequired: restore.restart_required,
    }
  }, mode)
  if (mode === 'verify') {
    assert.equal(result.health, 'ok')
    assert.equal(result.account, 'Release smoke')
    assert.equal(result.journal, 'Packaged restart persistence check')
    assert.equal(result.currency, 'USD')
  } else {
    assert.equal(result.accountBalance, '975.00')
    assert.equal(result.restoredAccount, true)
    assert.equal(result.discardedPostBackupAccount, false)
    assert.equal(result.restartRequired, true)
  }
  process.stdout.write(`${JSON.stringify({ mode, ...result }, null, 2)}\n`)
} finally {
  await browser.close()
}
