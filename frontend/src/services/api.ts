import axios from 'axios'

const runtimeApiBaseUrl = window.personalManager?.apiBaseUrl

export const api = axios.create({ baseURL: runtimeApiBaseUrl || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api', headers: { 'Content-Type': 'application/json' } })

export function getApiError(error: unknown, fallback = 'Không thể kết nối đến máy chủ.') {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}
