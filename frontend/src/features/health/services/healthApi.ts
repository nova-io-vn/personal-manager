import { api } from '../../../services/api'
import type { BodyMeasurement, BodyProfile, DailyHealthLog, Food, FoodLog, HealthSummary, MealType, NutritionSummary } from '../types/health'

export const healthApi = {
  getProfile: () => api.get<BodyProfile>('/health/profile').then((r) => r.data),
  saveProfile: (payload: Record<string, unknown>) => api.put<BodyProfile>('/health/profile', payload).then((r) => r.data),
  getSummary: (date: string) => api.get<HealthSummary>('/health/summary', { params: { date } }).then((r) => r.data),
  getMeasurements: () => api.get<BodyMeasurement[]>('/health/measurements').then((r) => r.data),
  createMeasurement: (payload: Record<string, unknown>) => api.post<BodyMeasurement>('/health/measurements', payload).then((r) => r.data),
  updateMeasurement: (id: number, payload: Record<string, unknown>) => api.patch<BodyMeasurement>(`/health/measurements/${id}`, payload).then((r) => r.data),
  deleteMeasurement: (id: number) => api.delete(`/health/measurements/${id}`),
  getDaily: (start?: string, end?: string) => api.get<DailyHealthLog[]>('/health/daily', { params: { start, end } }).then((r) => r.data),
  saveDaily: (date: string, payload: Record<string, unknown>) => api.put<DailyHealthLog>(`/health/daily/${date}`, payload).then((r) => r.data),
  getFoods: (search?: string) => api.get<Food[]>('/foods', { params: { search } }).then((r) => r.data),
  createFood: (payload: Record<string, unknown>) => api.post<Food>('/foods', payload).then((r) => r.data),
  updateFood: (id: number, payload: Record<string, unknown>) => api.patch<Food>(`/foods/${id}`, payload).then((r) => r.data),
  deleteFood: (id: number) => api.delete(`/foods/${id}`),
  getFoodLogs: (loggedDate: string, mealType?: MealType) => api.get<FoodLog[]>('/food-logs', { params: { logged_date: loggedDate, meal_type: mealType } }).then((r) => r.data),
  createFoodLog: (payload: Record<string, unknown>) => api.post<FoodLog>('/food-logs', payload).then((r) => r.data),
  deleteFoodLog: (id: number) => api.delete(`/food-logs/${id}`),
  getNutrition: (date: string) => api.get<NutritionSummary>('/nutrition/summary', { params: { date } }).then((r) => r.data),
}
