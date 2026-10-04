const { app, BrowserWindow, dialog, ipcMain } = require('electron')
const { spawn } = require('node:child_process')
const fs = require('node:fs/promises')
const net = require('node:net')
const path = require('node:path')

let mainWindow = null
let backendProcess = null
let apiBaseUrl = ''
let quitting = false

const singleInstance = app.requestSingleInstanceLock()
if (!singleInstance) app.quit()
if (singleInstance) app.on('second-instance', () => { if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus() } })

function availablePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref(); server.on('error', reject)
    server.listen(0, '127.0.0.1', () => { const address = server.address(); const port = typeof address === 'object' && address ? address.port : 0; server.close(() => resolve(port)) })
  })
}

function backendExecutable() {
  if (app.isPackaged) return path.join(process.resourcesPath, 'backend', 'personal-manager-backend.exe')
  return path.join(__dirname, '..', 'backend', 'dist', 'personal-manager-backend', 'personal-manager-backend.exe')
}

async function waitForBackend(healthUrl, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (backendProcess?.exitCode !== null) throw new Error('Dịch vụ backend đã dừng trong khi khởi động.')
    try { const response = await fetch(healthUrl); if (response.ok) return } catch { /* Retry while process initializes. */ }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error('Dịch vụ backend không sẵn sàng sau 30 giây.')
}

function stopBackend() {
  if (backendProcess && backendProcess.exitCode === null) backendProcess.kill()
  backendProcess = null
}

async function startBackend() {
  const port = await availablePort()
  apiBaseUrl = `http://127.0.0.1:${port}/api`
  backendProcess = spawn(backendExecutable(), ['--port', String(port)], {
    windowsHide: true,
    env: { ...process.env, PERSONAL_MANAGER_DATA_DIR: app.getPath('userData'), CORS_ORIGINS: 'null' },
    stdio: 'ignore',
  })
  await waitForBackend(`${apiBaseUrl}/health`)
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440, height: 920, minWidth: 1024, minHeight: 700, show: false,
    backgroundColor: '#f8fafc',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false,
      additionalArguments: [`--pm-api-base-url=${apiBaseUrl}`], sandbox: true,
    },
  })
  const frontend = app.isPackaged ? path.join(process.resourcesPath, 'frontend', 'dist', 'index.html') : path.join(__dirname, '..', 'frontend', 'dist', 'index.html')
  mainWindow.removeMenu(); mainWindow.loadFile(frontend)
  mainWindow.once('ready-to-show', () => mainWindow.show())
  mainWindow.on('closed', () => { mainWindow = null })
}

function filenameFromHeader(header) {
  const match = header?.match(/filename="?([^";]+)"?/)
  return match?.[1] || `personal-manager-backup-${new Date().toISOString().slice(0, 10)}.zip`
}

ipcMain.handle('data:create-backup', async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/data/backup`, { method: 'POST' })
    if (!response.ok) throw new Error('Backend rejected backup')
    const result = await dialog.showSaveDialog(mainWindow, { defaultPath: filenameFromHeader(response.headers.get('content-disposition')), filters: [{ name: 'Personal Manager Backup', extensions: ['zip'] }] })
    if (result.canceled || !result.filePath) return { success: false, message: 'Đã hủy sao lưu.' }
    await fs.writeFile(result.filePath, Buffer.from(await response.arrayBuffer()))
    return { success: true, message: 'Đã tạo bản sao lưu.' }
  } catch { return { success: false, message: 'Không thể tạo bản sao lưu.' } }
})

ipcMain.handle('data:restore-backup', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, { properties: ['openFile'], filters: [{ name: 'Personal Manager Backup', extensions: ['zip'] }] })
    if (result.canceled || !result.filePaths[0]) return { success: false, message: 'Đã hủy khôi phục.' }
    const bytes = await fs.readFile(result.filePaths[0]); const body = new FormData(); body.append('file', new Blob([bytes]), path.basename(result.filePaths[0]))
    const response = await fetch(`${apiBaseUrl}/data/restore`, { method: 'POST', body })
    const payload = await response.json()
    if (!response.ok) return { success: false, message: payload.detail || 'Bản sao lưu không hợp lệ.' }
    return { success: true, message: payload.message }
  } catch { return { success: false, message: 'Không thể khôi phục dữ liệu.' } }
})

if (singleInstance) app.whenReady().then(async () => {
  try { await startBackend(); createWindow() }
  catch (error) { dialog.showErrorBox('Personal Manager không thể khởi động', error instanceof Error ? error.message : 'Lỗi không xác định'); app.quit() }
})
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('before-quit', () => { if (!quitting) { quitting = true; stopBackend() } })
app.on('activate', () => { if (!mainWindow && apiBaseUrl) createWindow() })
