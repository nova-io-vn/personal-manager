export type DebtDirection = 'OWED_BY_ME' | 'OWED_TO_ME'
export interface Debt { id: number; person: string; direction: DebtDirection; amount: string; paid_amount: string; due_date: string | null; note: string | null; created_at: string; updated_at: string }
