import { useCallback, useEffect, useMemo, useState } from 'react'
import { BarChart3, Plus, RefreshCw } from 'lucide-react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { endOfMonth, format, startOfMonth } from 'date-fns'
import { vi } from 'date-fns/locale'
import { getApiError } from '../../../services/api'
import { AccountForm } from '../components/AccountForm'
import { AccountList } from '../components/AccountList'
import { BudgetProgress } from '../components/BudgetProgress'
import { FinanceSummaryCards } from '../components/FinanceSummaryCards'
import { TransactionForm } from '../components/TransactionForm'
import { TransactionTable } from '../components/TransactionTable'
import { financeApi } from '../services/financeApi'
import type { Account, Budget, Transaction, TransactionCategory } from '../types/finance'
import { formatVnd } from '../../../utils/format'
import { useLocation, useNavigate } from 'react-router-dom'

export function FinancePage() {
  const location = useLocation(); const navigate = useNavigate()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<TransactionCategory[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [transactionModal, setTransactionModal] = useState<Transaction | null | false>(false)
  const [accountModal, setAccountModal] = useState<Account | null | false>(false)
  const [busy, setBusy] = useState(false)
  const [filterType, setFilterType] = useState('')

  const loadData = useCallback(async () => { setLoading(true); setError(''); try { const [nextAccounts, nextCategories, nextTransactions, nextBudgets] = await Promise.all([financeApi.getAccounts(), financeApi.getCategories(), financeApi.getTransactions(), financeApi.getBudgets()]); setAccounts(nextAccounts); setCategories(nextCategories); setTransactions(nextTransactions); setBudgets(nextBudgets) } catch (err) { setError(getApiError(err)) } finally { setLoading(false) } }, [])
  // The effect synchronizes server data when the Finance page mounts.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void loadData() }, [loadData])
  // Consume the one-shot action encoded by the Quick Add navigation.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (new URLSearchParams(location.search).get('quickAdd') === 'transaction') { setTransactionModal(null); navigate('/finance', { replace: true }) } }, [location.search, navigate])

  const monthStart = format(startOfMonth(new Date()), 'yyyy-MM-dd')
  const monthEnd = format(endOfMonth(new Date()), 'yyyy-MM-dd')
  const monthTransactions = useMemo(() => transactions.filter((item) => item.transaction_date >= monthStart && item.transaction_date <= monthEnd), [transactions, monthStart, monthEnd])
  const monthIncome = monthTransactions.filter((item) => item.type === 'INCOME').reduce((sum, item) => sum + Number(item.amount), 0)
  const monthExpense = monthTransactions.filter((item) => item.type === 'EXPENSE').reduce((sum, item) => sum + Number(item.amount), 0)
  const totalBalance = accounts.reduce((sum, item) => sum + Number(item.current_balance), 0)
  const totalBudget = budgets.filter((item) => item.start_date <= monthEnd && item.end_date >= monthStart).reduce((sum, item) => sum + Number(item.amount), 0)
  const filteredTransactions = filterType ? transactions.filter((item) => item.type === filterType) : transactions
  const expenseByCategory = categories.filter((item) => item.type === 'EXPENSE').map((category) => ({ name: category.name, value: monthTransactions.filter((item) => item.type === 'EXPENSE' && item.category_id === category.id).reduce((sum, item) => sum + Number(item.amount), 0) })).filter((item) => item.value > 0)
  const chartData = [{ name: 'Thu', value: monthIncome }, { name: 'Chi', value: monthExpense }]

  const submitTransaction = async (payload: Record<string, unknown>, id?: number) => { setBusy(true); try { if (id) await financeApi.updateTransaction(id, payload); else await financeApi.createTransaction(payload); setTransactionModal(false); await loadData() } catch (err) { setError(getApiError(err)) } finally { setBusy(false) } }
  const submitAccount = async (payload: { name: string; type: 'CASH' | 'BANK' | 'EWALLET'; initial_balance: string }, id?: number) => { setBusy(true); try { if (id) await financeApi.updateAccount(id, { name: payload.name, type: payload.type }); else await financeApi.createAccount(payload); setAccountModal(false); await loadData() } catch (err) { setError(getApiError(err)) } finally { setBusy(false) } }
  const removeTransaction = async (item: Transaction) => { if (!window.confirm('Xóa giao dịch này?')) return; try { await financeApi.deleteTransaction(item.id); await loadData() } catch (err) { setError(getApiError(err)) } }
  const removeAccount = async (item: Account) => { if (!window.confirm(`Xóa tài khoản ${item.name}?`)) return; try { await financeApi.deleteAccount(item.id); await loadData() } catch (err) { setError(getApiError(err)) } }
  const removeBudget = async (item: Budget) => { if (!window.confirm('Xóa ngân sách này?')) return; try { await financeApi.deleteBudget(item.id); await loadData() } catch (err) { setError(getApiError(err)) } }

  if (loading) return <div className="page-content"><div className="card flex min-h-[420px] items-center justify-center text-sm text-slate-400">Đang tải dữ liệu tài chính…</div></div>
  if (error && !accounts.length && !transactions.length) return <div className="page-content"><div className="card flex min-h-[420px] flex-col items-center justify-center gap-3 text-center"><p className="font-bold text-slate-700">Không thể tải dữ liệu tài chính</p><p className="text-sm text-slate-500">{error}</p><button className="button-secondary" onClick={() => void loadData()}><RefreshCw size={15} /> Thử lại</button></div></div>
  return <div className="page-content"><div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold text-blue-600">{format(new Date(), 'EEEE, dd/MM/yyyy', { locale: vi })}</p><h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-800">Tài chính</h2><p className="mt-1 text-sm text-slate-500">Theo dõi thu nhập, chi tiêu và ngân sách của bạn.</p></div><div className="flex gap-2"><button className="button-secondary" onClick={() => setAccountModal(null)}><Plus size={16} /> Tài khoản</button><button className="button-primary" onClick={() => setTransactionModal(null)}><Plus size={16} /> Thêm giao dịch</button></div></div>{error && <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>}<FinanceSummaryCards balance={totalBalance} income={monthIncome} expense={monthExpense} budget={totalBudget - monthExpense} /><div className="mt-5 grid gap-5 xl:grid-cols-[1.4fr_1fr]"><div className="card p-5"><div className="flex items-center justify-between"><div><h3 className="font-bold text-slate-800">Thu nhập và chi tiêu</h3><p className="mt-0.5 text-xs text-slate-400">Tháng hiện tại</p></div><BarChart3 size={19} className="text-slate-400" /></div>{monthIncome + monthExpense === 0 ? <div className="flex h-64 items-center justify-center text-sm text-slate-400">Chưa có dữ liệu trong tháng này.</div> : <ResponsiveContainer width="100%" height={260}><BarChart data={chartData} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}><CartesianGrid vertical={false} stroke="#edf1f6" /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#7b8798', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#7b8798', fontSize: 11 }} tickFormatter={(value: number) => `${Math.round(value / 1000)}k`} /><Tooltip formatter={(value) => formatVnd(Number(value))} /><Bar dataKey="value" fill="#557bd9" radius={[5, 5, 0, 0]} barSize={54} /></BarChart></ResponsiveContainer>}</div><div className="card p-5"><h3 className="font-bold text-slate-800">Chi tiêu theo danh mục</h3><p className="mt-0.5 text-xs text-slate-400">Tháng hiện tại</p>{expenseByCategory.length === 0 ? <div className="flex h-64 items-center justify-center text-sm text-slate-400">Chưa có dữ liệu chi tiêu.</div> : <ResponsiveContainer width="100%" height={260}><PieChart><Pie data={expenseByCategory} dataKey="value" nameKey="name" innerRadius={62} outerRadius={90} paddingAngle={3}>{expenseByCategory.map((entry, index) => <Cell key={entry.name} fill={['#557bd9', '#62b58d', '#e39a4a', '#d96969', '#8a72d8', '#6e9faf'][index % 6]} />)}</Pie><Tooltip formatter={(value) => formatVnd(Number(value))} /></PieChart></ResponsiveContainer>}<div className="flex flex-wrap justify-center gap-x-4 gap-y-1">{expenseByCategory.slice(0, 5).map((item) => <span className="text-xs text-slate-500" key={item.name}>• {item.name}</span>)}</div></div></div><div className="mt-5 grid gap-5 xl:grid-cols-[1fr_1.35fr]"><AccountList accounts={accounts} onEdit={(item) => setAccountModal(item)} onDelete={(item) => void removeAccount(item)} /><BudgetProgress budgets={budgets} categories={categories} transactions={transactions} onDelete={(item) => void removeBudget(item)} /></div><div className="mt-5"><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-bold text-slate-800">Giao dịch</h3><p className="text-xs text-slate-400">Lịch sử giao dịch từ Finance API</p></div><select className="field w-auto min-w-[150px] py-2 text-sm" value={filterType} onChange={(event) => setFilterType(event.target.value)}><option value="">Tất cả loại</option><option value="INCOME">Thu nhập</option><option value="EXPENSE">Chi tiêu</option><option value="TRANSFER">Chuyển khoản</option></select></div><TransactionTable transactions={filteredTransactions} accounts={accounts} categories={categories} onEdit={(item) => setTransactionModal(item)} onDelete={(item) => void removeTransaction(item)} /></div>{transactionModal !== false && <TransactionForm accounts={accounts} categories={categories} editing={transactionModal} onClose={() => setTransactionModal(false)} onSubmit={submitTransaction} busy={busy} />}{accountModal !== false && <AccountForm editing={accountModal} onClose={() => setAccountModal(false)} onSubmit={submitAccount} busy={busy} />}</div>
}
