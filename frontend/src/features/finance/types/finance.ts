export type AccountType = 'CASH' | 'BANK' | 'EWALLET'
export type CategoryType = 'INCOME' | 'EXPENSE'
export type TransactionType = 'INCOME' | 'EXPENSE' | 'TRANSFER'
export type TransactionSource = 'MANUAL' | 'BANK_IMPORT' | 'AI'

export interface Account { id: number; name: string; type: AccountType; initial_balance: string; current_balance: string; created_at: string; updated_at: string }
export interface TransactionCategory { id: number; name: string; type: CategoryType; icon: string | null; color: string | null; created_at: string }
export interface Transaction { id: number; account_id: number; category_id: number | null; related_account_id: number | null; type: TransactionType; amount: string; description: string | null; transaction_date: string; source: TransactionSource; created_at: string; updated_at: string }
export interface Budget { id: number; category_id: number; amount: string; period: string; start_date: string; end_date: string; created_at: string; updated_at: string }
export interface TransactionFilters { start_date?: string; end_date?: string; account_id?: number; category_id?: number; type?: TransactionType }

export const accountLabels: Record<AccountType, string> = { CASH: 'Tiền mặt', BANK: 'Ngân hàng', EWALLET: 'Ví điện tử' }
export const transactionLabels: Record<TransactionType, string> = { INCOME: 'Thu nhập', EXPENSE: 'Chi tiêu', TRANSFER: 'Chuyển khoản' }
