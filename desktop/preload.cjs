const { contextBridge, ipcRenderer } = require('electron')

const argument = process.argv.find((value) => value.startsWith('--pm-api-base-url='))
const apiBaseUrl = argument ? argument.slice('--pm-api-base-url='.length) : 'http://127.0.0.1:8000/api'

contextBridge.exposeInMainWorld('personalManager', Object.freeze({
  apiBaseUrl,
  createBackup: () => ipcRenderer.invoke('data:create-backup'),
  restoreBackup: () => ipcRenderer.invoke('data:restore-backup'),
}))
