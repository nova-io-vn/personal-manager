export type Sex = 'MALE' | 'FEMALE'
export type ActivityLevel = 'SEDENTARY' | 'LIGHT' | 'MODERATE' | 'ACTIVE' | 'VERY_ACTIVE'
export type HealthGoal = 'LOSE_WEIGHT' | 'MAINTAIN' | 'GAIN_WEIGHT'
export type MealType = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'SNACK'

export interface BodyProfile { id: number; height_cm: string; weight_kg: string; age: number; sex: Sex; activity_level: ActivityLevel; goal: HealthGoal; created_at: string; updated_at: string }
export interface BodyMeasurement { id: number; weight_kg: string; waist_cm: string | null; note: string | null; recorded_at: string; created_at: string }
export interface DailyHealthLog { id: number; date: string; sleep_hours: string | null; water_ml: number | null; steps: number | null; exercise_type: string | null; exercise_minutes: number | null; note: string | null; created_at: string; updated_at: string }
export interface Food { id: number; name: string; serving_quantity: string; serving_unit: string; calories: string; protein: string; carbs: string; fat: string; created_at: string; updated_at: string }
export interface FoodLog { id: number; food_id: number; quantity: string; meal_type: MealType; logged_date: string; created_at: string; food: Food }
export interface NutritionTotals { calories: string; protein: string; carbs: string; fat: string }
export interface NutritionSummary extends NutritionTotals { date: string; meals: Record<MealType, FoodLog[]> }
export interface HealthSummary { profile: BodyProfile | null; metrics: { bmi: string; bmr: string; tdee: string; target_calories: string } | null; weight: string | null; weight_change: string | null; today: DailyHealthLog | null; nutrition: NutritionTotals }

export const activityLabels: Record<ActivityLevel, string> = { SEDENTARY: 'Ít vận động', LIGHT: 'Vận động nhẹ', MODERATE: 'Vận động vừa', ACTIVE: 'Vận động nhiều', VERY_ACTIVE: 'Vận động rất nhiều' }
export const goalLabels: Record<HealthGoal, string> = { LOSE_WEIGHT: 'Giảm cân', MAINTAIN: 'Duy trì', GAIN_WEIGHT: 'Tăng cân' }
export const mealLabels: Record<MealType, string> = { BREAKFAST: 'Bữa sáng', LUNCH: 'Bữa trưa', DINNER: 'Bữa tối', SNACK: 'Ăn nhẹ' }
