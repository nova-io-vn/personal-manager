import { api } from '../../../services/api'

export interface AIResponse { answer: string; context_domains: string[] }

export const aiApi = {
  chat: (message: string) => api.post<AIResponse>('/ai/chat', { message }).then((response) => response.data),
}
