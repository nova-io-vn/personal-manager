export interface AppSettings {
  currency: string
  default_reminder_minutes: number
  notifications_enabled: boolean
  schedule_reminders_enabled: boolean
  budget_warnings_enabled: boolean
  journal_reminder_enabled: boolean
  journal_reminder_time: string
  health_reminder_enabled: boolean
  health_reminder_time: string
  daily_summary_enabled: boolean
  daily_summary_time: string
  telegram_enabled: boolean
  telegram_bot_token: string | null
  telegram_token_configured: boolean
  telegram_chat_id: string | null
  gemini_enabled: boolean
  gemini_api_key: string | null
  gemini_key_configured: boolean
  gemini_model: string
}

export type NotificationEventType = 'SCHEDULE_REMINDER' | 'BUDGET_WARNING' | 'JOURNAL_REMINDER' | 'HEALTH_REMINDER' | 'DAILY_SUMMARY'
export type NotificationChannel = 'LOCAL' | 'TELEGRAM'
export type NotificationStatus = 'PENDING' | 'SENT' | 'FAILED' | 'CANCELLED'
export interface AppNotification { id: number; event_type: NotificationEventType; channel: NotificationChannel; title: string; message: string; scheduled_for: string; sent_at: string | null; status: NotificationStatus; related_entity_type: string | null; related_entity_id: number | null; read_at: string | null; created_at: string }
