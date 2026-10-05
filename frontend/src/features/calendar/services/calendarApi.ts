import { api } from '../../../services/api'
import type { Schedule, ScheduleCategory } from '../types/calendar'

export const calendarApi = {
  getCategories: () => api.get<ScheduleCategory[]>('/schedule-categories').then((r) => r.data),
  getSchedules: (params: { start: string; end: string }) => api.get<Schedule[]>('/schedules', { params }).then((r) => r.data),
  getSchedule: (id: number) => api.get<Schedule>(`/schedules/${id}`).then((r) => r.data),
  createSchedule: (payload: Record<string, unknown>) => api.post<Schedule>('/schedules', payload).then((r) => r.data),
  updateSchedule: (id: number, payload: Record<string, unknown>) => api.patch<Schedule>(`/schedules/${id}`, payload).then((r) => r.data),
  setOccurrenceCompleted: (id: number, occurrenceStart: string, completed: boolean) => api.patch<Schedule>(`/schedules/${id}/occurrence-completion`, { occurrence_start: occurrenceStart, completed }).then((r) => r.data),
  deleteSchedule: (id: number) => api.delete(`/schedules/${id}`),
}
