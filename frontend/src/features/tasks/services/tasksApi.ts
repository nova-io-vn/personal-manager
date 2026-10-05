import { api } from '../../../services/api'
import type { Task } from '../types/tasks'

export const tasksApi = {
  getTasks: (includeCompleted = true) => api.get<Task[]>('/tasks', { params: { include_completed: includeCompleted } }).then((response) => response.data),
  createTask: (payload: { title: string; note?: string | null; due_date?: string | null }) => api.post<Task>('/tasks', payload).then((response) => response.data),
  updateTask: (id: number, payload: Partial<Pick<Task, 'title' | 'note' | 'due_date' | 'completed'>>) => api.patch<Task>(`/tasks/${id}`, payload).then((response) => response.data),
  deleteTask: (id: number) => api.delete(`/tasks/${id}`),
}
