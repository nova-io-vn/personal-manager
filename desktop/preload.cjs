const { contextBridge, ipcRenderer } = require('electron')

const argument = process.argv.find((value) => value.startsWith('--pm-api-base-url='))
const apiBaseUrl = argument ? argument.slice('--pm-api-base-url='.length) : (process.env.PM_API_BASE_URL || 'https://personal.nova.io.vn/api')

contextBridge.exposeInMainWorld('personalManager', Object.freeze({
  apiBaseUrl,
  getVersion: () => ipcRenderer.invoke('app:version'),
  checkForUpdates: () => ipcRenderer.invoke('app:check-updates'),
  downloadUpdate: () => ipcRenderer.invoke('app:download-update'),
  installUpdate: () => ipcRenderer.invoke('app:install-update'),
  onUpdateAvailable: (callback) => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('app:update-available', listener)
    return () => ipcRenderer.removeListener('app:update-available', listener)
  },
  onUpdateDownloaded: (callback) => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('app:update-downloaded', listener)
    return () => ipcRenderer.removeListener('app:update-downloaded', listener)
  },
  createBackup: () => ipcRenderer.invoke('data:create-backup'),
  restoreBackup: () => ipcRenderer.invoke('data:restore-backup'),
}))
