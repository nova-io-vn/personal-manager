export type Mood = 'VERY_BAD' | 'BAD' | 'NEUTRAL' | 'GOOD' | 'VERY_GOOD'
export interface JournalTag { id: number; name: string; created_at: string }
export interface JournalEntry { id: number; entry_date: string; mood: Mood; content: string; tags: JournalTag[]; created_at: string; updated_at: string }
export const moodOptions: Array<{ value: Mood; emoji: string; label: string }> = [{ value: 'VERY_BAD', emoji: '😞', label: 'Rất tệ' }, { value: 'BAD', emoji: '🙁', label: 'Không tốt' }, { value: 'NEUTRAL', emoji: '😐', label: 'Bình thường' }, { value: 'GOOD', emoji: '🙂', label: 'Tốt' }, { value: 'VERY_GOOD', emoji: '😄', label: 'Rất tốt' }]
