import { expect, test } from '@playwright/test'

test('application navigation, notification center, safe settings persistence', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: /Tổng quan/i })).toBeVisible()
  await page.getByRole('link', { name: /Tài chính/i }).click()
  await expect(page.getByRole('heading', { level: 2, name: /Tài chính/i })).toBeVisible()
  await page.getByRole('link', { name: /Sức khỏe/i }).click()
  await expect(page.getByRole('heading', { level: 2, name: /Cơ thể, dinh dưỡng/i })).toBeVisible()
  await page.getByRole('link', { name: /Nhật ký/i }).click()
  await expect(page.getByRole('heading', { level: 2, name: /Nhật ký/i })).toBeVisible()
  await page.getByRole('link', { name: /Cài đặt/i }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Cài đặt' })).toBeVisible()
  await page.getByLabel('Model').fill('gemini-3.5-flash')
  await page.getByRole('button', { name: 'Lưu cài đặt' }).click()
  await expect(page.getByText(/Đã lưu cấu hình/i)).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Model')).toHaveValue('gemini-3.5-flash')
  await page.getByRole('button', { name: /thông báo|notifications/i }).click()
  await expect(page.getByText(/thông báo gần đây|20 gần nhất/i)).toBeVisible()
})

test('finance account and expense persist with authoritative balance', async ({ page, request }) => {
  const suffix = Date.now()
  await page.goto('/finance')
  await page.getByRole('button', { name: /Tài khoản/i }).click()
  await page.locator('#account-name').fill(`E2E Cash ${suffix}`)
  await page.locator('#account-type').selectOption('CASH')
  await page.locator('#account-balance').fill('1000')
  await Promise.all([
    page.waitForResponse((response) => response.url().includes('/api/accounts') && response.request().method() === 'POST'),
    page.getByRole('button', { name: /Lưu tài khoản/i }).click(),
  ])
  await expect(page.getByText(`E2E Cash ${suffix}`)).toBeVisible()
  await page.getByRole('button', { name: /Thêm giao dịch/i }).click()
  await page.locator('#transaction-type').selectOption('EXPENSE')
  await page.locator('#transaction-amount').fill('125')
  await page.locator('#transaction-description').fill('E2E lunch')
  await Promise.all([
    page.waitForResponse((response) => response.url().includes('/api/transactions') && response.request().method() === 'POST'),
    page.getByRole('button', { name: /Lưu giao dịch/i }).click(),
  ])
  const accounts = await request.get('http://127.0.0.1:18766/api/accounts').then((response) => response.json()) as Array<{ name: string; current_balance: string }>
  expect(accounts.find((account) => account.name === `E2E Cash ${suffix}`)?.current_balance).toBe('875.00')
})

test('calendar create recurrence displays virtual week occurrence', async ({ page, request }) => {
  const start = new Date(); start.setDate(start.getDate() - start.getDay() + 1); start.setHours(11, 0, 0, 0)
  await page.clock.install({ time: new Date(start.getFullYear(), start.getMonth(), start.getDate(), 11, 30) })
  const end = new Date(start); end.setHours(12)
  const startValue = (date: Date) => { const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000); return local.toISOString().slice(0, 16) }
  await page.goto('/calendar')
  const mondayColumn = page.locator('.calendar-day-column').first()
  await mondayColumn.click({ position: { x: 48, y: 11 * 88 + 8 } })
  await expect(page.locator('#schedule-title')).toBeVisible()
  await page.locator('#schedule-title').fill('E2E weekly review')
  await page.locator('#schedule-start').fill(startValue(start))
  await page.locator('#schedule-end').fill(startValue(end))
  await page.locator('#schedule-repeat').selectOption('WEEKLY')
  await page.getByRole('button', { name: /Lưu lịch trình/i }).click()
  const rangeStart = new Date(start); rangeStart.setDate(rangeStart.getDate() - 1)
  const rangeEnd = new Date(start); rangeEnd.setDate(rangeEnd.getDate() + 8)
  const params = new URLSearchParams({ start: rangeStart.toISOString(), end: rangeEnd.toISOString() })
  const result = await request.get(`http://127.0.0.1:18766/api/schedules?${params}`).then((response) => response.json()) as Array<{ title: string }>
  expect(result.some((event) => event.title === 'E2E weekly review')).toBeTruthy()
  await expect(page.getByText('Đang diễn ra', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Đánh dấu hoàn thành: E2E weekly review' }).click()
  await expect(page.getByRole('button', { name: 'Bỏ hoàn thành: E2E weekly review' })).toBeVisible()
  const refreshed = await request.get(`http://127.0.0.1:18766/api/schedules?${params}`).then((response) => response.json()) as Array<{ title: string; completed: boolean }>
  expect(refreshed.find((event) => event.title === 'E2E weekly review')?.completed).toBe(true)
})

test('calendar adapts to a portrait tablet without page-level horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 800, height: 1280 })
  await page.goto('/calendar')
  await expect(page.getByRole('heading', { level: 2, name: /Lịch trình/i })).toBeVisible()
  await expect(page.locator('.calendar-scroll')).toBeVisible()
  const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth)
  expect(pageWidth).toBeLessThanOrEqual(800)
})

test('health, nutrition and journal forms persist through backend', async ({ page, request }) => {
  await page.goto('/health')
  await page.getByRole('button', { name: /Thêm hồ sơ sức khỏe/i }).click()
  await page.locator('#profile-height').fill('172')
  await page.locator('#profile-weight').fill('68')
  await page.locator('#profile-age').fill('30')
  expect(await page.locator('form.modal').evaluate((form) => (form as HTMLFormElement).checkValidity())).toBeTruthy()
  const profileResponse = page.waitForResponse((response) => response.url().includes('/health/profile') && response.request().method() === 'PUT', { timeout: 5000 })
  await page.getByRole('button', { name: /^Lưu$/i }).click()
  const savedProfile = await profileResponse
  expect(savedProfile.status(), await savedProfile.text()).toBe(200)
  await expect(page.getByText('BMI', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /Dinh dưỡng/i }).click()
  await page.getByRole('button', { name: /Thực phẩm/i }).click()
  await page.locator('#food-name').fill('E2E oats')
  await page.locator('#food-calories').fill('150')
  await Promise.all([
    page.waitForResponse((response) => response.url().includes('/api/foods') && response.request().method() === 'POST'),
    page.getByRole('button', { name: /^Lưu$/i }).click(),
  ])
  await page.getByRole('button', { name: /Ghi bữa ăn/i }).click()
  await page.locator('#log-quantity').fill('100')
  await Promise.all([
    page.waitForResponse((response) => response.url().includes('/api/food-logs') && response.request().method() === 'POST'),
    page.getByRole('button', { name: /^Lưu$/i }).click(),
  ])
  const nutrition = await request.get('http://127.0.0.1:18766/api/nutrition/summary').then((response) => response.json()) as { calories: string }
  expect(Number(nutrition.calories)).toBeGreaterThanOrEqual(150)
  await page.getByRole('link', { name: /Nhật ký/i }).click()
  const canvas = page.locator('canvas.drawing-canvas')
  await expect(canvas).toBeVisible()
  const box = await canvas.boundingBox()
  expect(box).not.toBeNull()
  if (box) {
    await page.mouse.move(box.x + 80, box.y + 80)
    await page.mouse.down()
    await page.mouse.move(box.x + 220, box.y + 160, { steps: 8 })
    await page.mouse.up()
  }
  await page.getByRole('button', { name: /Lưu trang nhật ký/i }).click()
  await page.reload()
  await expect(page.locator('canvas.drawing-canvas')).toBeVisible()
  const entries = await request.get('http://127.0.0.1:18766/api/journals').then((response) => response.json()) as Array<{ drawing_data: string | null }>
  expect(entries.some((entry) => entry.drawing_data?.startsWith('data:image/png'))).toBeTruthy()
})
