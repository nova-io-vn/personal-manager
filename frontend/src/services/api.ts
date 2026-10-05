import axios from 'axios'
import { Capacitor } from '@capacitor/core'

const runtimeApiBaseUrl = window.personalManager?.apiBaseUrl
export const isAndroid = Capacitor.getPlatform() === 'android'
// Android and packaged Desktop use the shared FastAPI service. The old local
// adapter remains only as legacy code and is not used by release builds.
export const isOfflineAndroid = false

export const api = axios.create({
  baseURL: runtimeApiBaseUrl || import.meta.env.VITE_API_BASE_URL || 'https://personal.nova.io.vn/api',
  headers: { 'Content-Type': 'application/json' },
})

export function getApiError(error: unknown, fallback = 'Không thể kết nối đến máy chủ.') {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}
