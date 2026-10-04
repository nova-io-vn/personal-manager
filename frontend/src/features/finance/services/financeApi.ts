import { api } from '../../../services/api'
import type { Account, AccountType, Budget, Transaction, TransactionCategory, TransactionFilters, TransactionType } from '../types/finance'

export const financeApi = {
  getAccounts: () => api.get<Account[]>('/accounts').then((r) => r.data),
  createAccount: (payload: { name: string; type: AccountType; initial_balance: string }) => api.post<Account>('/accounts', payload).then((r) => r.data),
  updateAccount: (id: number, payload: { name?: string; type?: AccountType }) => api.patch<Account>(`/accounts/${id}`, payload).then((r) => r.data),
  deleteAccount: (id: number) => api.delete(`/accounts/${id}`),
  getCategories: () => api.get<TransactionCategory[]>('/transaction-categories').then((r) => r.data),
  getTransactions: (filters: TransactionFilters = {}) => api.get<Transaction[]>('/transactions', { params: filters }).then((r) => r.data),
  createTransaction: (payload: Record<string, unknown>) => api.post<Transaction>('/transactions', payload).then((r) => r.data),
  updateTransaction: (id: number, payload: Record<string, unknown>) => api.patch<Transaction>(`/transactions/${id}`, payload).then((r) => r.data),
  deleteTransaction: (id: number) => api.delete(`/transactions/${id}`),
  getBudgets: () => api.get<Budget[]>('/budgets').then((r) => r.data),
  createBudget: (payload: { category_id: number; amount: string; period: string; start_date: string; end_date: string }) => api.post<Budget>('/budgets', payload).then((r) => r.data),
  updateBudget: (id: number, payload: Record<string, unknown>) => api.patch<Budget>(`/budgets/${id}`, payload).then((r) => r.data),
  deleteBudget: (id: number) => api.delete(`/budgets/${id}`),
}

export function transactionPayload(type: TransactionType, values: { account_id: number; related_account_id?: number; category_id?: number; amount: string; transaction_date: string; description?: string }) {
  return type === 'TRANSFER' ? { account_id: values.account_id, related_account_id: values.related_account_id, type, amount: values.amount, transaction_date: values.transaction_date, description: values.description || null } : { account_id: values.account_id, category_id: values.category_id, type, amount: values.amount, transaction_date: values.transaction_date, description: values.description || null }
}
