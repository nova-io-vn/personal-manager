/// <reference types="vite/client" />

interface PersonalManagerDesktopApi {
  apiBaseUrl: string
  createBackup: () => Promise<{ success: boolean; message: string }>
  restoreBackup: () => Promise<{ success: boolean; message: string }>
}

interface Window {
  personalManager?: PersonalManagerDesktopApi
}
