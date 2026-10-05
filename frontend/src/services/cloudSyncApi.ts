import axios from 'axios'

const localStorageToken = 'personal-manager.cloud.access-token'
const localStorageDevice = 'personal-manager.cloud.device-key'

const runtimeBaseUrl = window.personalManager?.cloudApiBaseUrl
const baseURL = runtimeBaseUrl || import.meta.env.VITE_CLOUD_SYNC_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const cloudApi = axios.create({ baseURL, headers: { 'Content-Type': 'application/json' } })

function deviceKey() {
  const existing = localStorage.getItem(localStorageDevice)
  if (existing) return existing
  const created = crypto.randomUUID()
  localStorage.setItem(localStorageDevice, created)
  return created
}

cloudApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(localStorageToken)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export type CloudAuth = { access_token: string; device_id: string; user: { id: string; email: string } }
export type SyncChange = { entity_type: string; entity_id: string; operation: 'UPSERT' | 'DELETE'; payload: Record<string, unknown>; idempotency_key: string; occurred_at?: string }

export const cloudSyncApi = {
  isConfigured: Boolean(runtimeBaseUrl || import.meta.env.VITE_CLOUD_SYNC_API_URL),
  register: async (email: string, password: string) => {
    const response = await cloudApi.post<CloudAuth>('/auth/register', { email, password })
    localStorage.setItem(localStorageToken, response.data.access_token)
    return response.data
  },
  login: async (email: string, password: string, platform: 'desktop' | 'android') => {
    const response = await cloudApi.post<CloudAuth>('/auth/login', { email, password, device_key: deviceKey(), device_name: `Personal Manager ${platform}`, platform })
    localStorage.setItem(localStorageToken, response.data.access_token)
    return response.data
  },
  logout: () => localStorage.removeItem(localStorageToken),
  token: () => localStorage.getItem(localStorageToken),
  push: async (deviceId: string, changes: SyncChange[]) => (await cloudApi.post<{ accepted: number; duplicates: number; cursor: number }>('/sync/push', { device_id: deviceId, changes })).data,
  pull: async (cursor = 0) => (await cloudApi.get<{ changes: Array<SyncChange & { cursor: number; device_id: string }>; next_cursor: number }>('/sync/pull', { params: { cursor } })).data,
}
