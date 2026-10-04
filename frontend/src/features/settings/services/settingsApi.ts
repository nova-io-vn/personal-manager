import { api } from '../../../services/api'
import type { AppNotification, AppSettings } from '../types/settings'

export const settingsApi = {
  get: () => api.get<AppSettings>('/settings').then((r) => r.data),
  update: (payload: Partial<AppSettings> & { telegram_bot_token?: string | null; gemini_api_key?: string | null }) => api.patch<AppSettings>('/settings', payload).then((r) => r.data),
  testTelegram: () => api.post<{ success: boolean; message: string }>('/settings/telegram/test').then((r) => r.data),
  testGemini: () => api.post<{ success: boolean; message: string }>('/settings/gemini/test').then((r) => r.data),
}

export const dataApi = {
  latestBackup: () => api.get<{ filename: string; created_at: string; size_bytes: number } | null>('/data/backups/latest').then((r) => r.data),
  createBackup: () => api.post<Blob>('/data/backup', undefined, { responseType: 'blob' }).then((r) => ({ blob: r.data, disposition: r.headers['content-disposition'] as string | undefined })),
  restoreBackup: (file: File) => { const body = new FormData(); body.append('file', file); return api.post<{ success: boolean; message: string }>('/data/restore', body).then((r) => r.data) },
}

export const notificationApi = {
  list: (params: { limit?: number; unread_only?: boolean } = {}) => api.get<AppNotification[]>('/notifications', { params }).then((r) => r.data),
  markRead: (id: number) => api.patch<AppNotification>(`/notifications/${id}/read`).then((r) => r.data),
  remove: (id: number) => api.delete(`/notifications/${id}`),
}
