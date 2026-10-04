export type RepeatType = 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY'
export interface ScheduleCategory { id: number; name: string; color: string; created_at: string }
export interface Schedule { id: number; title: string; description: string | null; start_datetime: string; end_datetime: string; category_id: number | null; color: string | null; reminder_minutes: number; repeat_type: RepeatType; repeat_until: string | null; completed: boolean; created_at: string; updated_at: string; series_start_datetime?: string | null; is_recurring_occurrence?: boolean }
