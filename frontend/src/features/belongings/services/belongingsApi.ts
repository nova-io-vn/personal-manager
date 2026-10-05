import { api } from '../../../services/api'
import type { PersonalItem, PersonalItemPayload } from '../types/belongings'

export const belongingsApi = {
  getItems: () => api.get<PersonalItem[]>('/belongings').then((response) => response.data),
  createItem: (payload: PersonalItemPayload) => api.post<PersonalItem>('/belongings', payload).then((response) => response.data),
  updateItem: (id: number, payload: Partial<PersonalItemPayload>) => api.patch<PersonalItem>(`/belongings/${id}`, payload).then((response) => response.data),
  deleteItem: (id: number) => api.delete(`/belongings/${id}`),
}
