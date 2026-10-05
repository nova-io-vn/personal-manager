import { api } from '../../../services/api'
import type { JournalEntry, JournalTag, Mood } from '../types/journal'

export const journalApi = {
  getEntries: (params: { start_date?: string; end_date?: string; mood?: Mood; tag?: string } = {}) => api.get<JournalEntry[]>('/journals', { params }).then((r) => r.data),
  getEntry: (date: string) => api.get<JournalEntry>(`/journals/${date}`).then((r) => r.data),
  saveEntry: (date: string, payload: { mood: Mood; content: string; tag_ids: number[]; drawing_data?: string | null }) => api.put<JournalEntry>(`/journals/${date}`, payload).then((r) => r.data),
  deleteEntry: (date: string) => api.delete(`/journals/${date}`),
  getTags: () => api.get<JournalTag[]>('/journal-tags').then((r) => r.data),
  createTag: (name: string) => api.post<JournalTag>('/journal-tags', { name }).then((r) => r.data),
}
