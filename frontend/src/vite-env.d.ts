/// <reference types="vite/client" />

interface PersonalManagerDesktopApi {
  apiBaseUrl: string
  getVersion: () => Promise<string>
  checkForUpdates: () => Promise<{ supported: boolean; available?: boolean; version?: string; error?: string }>
  downloadUpdate: () => Promise<{ success: boolean; message?: string }>
  installUpdate: () => Promise<void>
  onUpdateAvailable: (callback: (payload: { version: string }) => void) => () => void
  onUpdateDownloaded: (callback: (payload: { version: string }) => void) => () => void
  createBackup: () => Promise<{ success: boolean; message: string }>
  restoreBackup: () => Promise<{ success: boolean; message: string }>
}

interface Window {
  personalManager?: PersonalManagerDesktopApi
}
