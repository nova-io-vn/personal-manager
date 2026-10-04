import { ArrowDownLeft, ArrowUpRight, Landmark, PiggyBank } from 'lucide-react'
import { formatVnd } from '../../../utils/format'

export function FinanceSummaryCards({ balance, income, expense, budget }: { balance: number; income: number; expense: number; budget: number }) {
  const cards = [{ label: 'Tổng số dư', value: balance, icon: Landmark, color: 'text-blue-600', bg: 'bg-blue-50' }, { label: 'Thu tháng này', value: income, icon: ArrowUpRight, color: 'text-emerald-600', bg: 'bg-emerald-50' }, { label: 'Chi tháng này', value: expense, icon: ArrowDownLeft, color: 'text-rose-600', bg: 'bg-rose-50' }, { label: 'Ngân sách còn lại', value: budget, icon: PiggyBank, color: 'text-violet-600', bg: 'bg-violet-50' }]
  return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, icon: Icon, color, bg }, index) => <div className={`card finance-summary-card ${index === 0 ? 'metric-primary' : ''} flex items-start justify-between p-5`} key={label}><div><p className="text-xs font-semibold text-slate-400">{label}</p><p className="mt-2 text-2xl font-bold tracking-tight text-slate-800">{formatVnd(value)}</p></div><div className={`grid h-10 w-10 place-items-center rounded-xl ${bg} ${color}`}><Icon size={19} /></div></div>)}</div>
}
