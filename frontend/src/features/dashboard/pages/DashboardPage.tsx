import { useEffect, useState } from 'react'
import { addDays, endOfDay, format, isAfter, startOfDay } from 'date-fns'
import { vi } from 'date-fns/locale'
import { Activity, ArrowDownLeft, ArrowUpRight, BookOpen, CalendarDays, ChevronRight, Clock3, Droplets, Moon, Plus, Sparkles, WalletCards } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getApiError } from '../../../services/api'
import { formatVnd } from '../../../utils/format'
import { calendarApi } from '../../calendar/services/calendarApi'
import type { Schedule } from '../../calendar/types/calendar'
import { financeApi } from '../../finance/services/financeApi'
import type { Account, Transaction } from '../../finance/types/finance'
import { healthApi } from '../../health/services/healthApi'
import type { HealthSummary } from '../../health/types/health'
import { journalApi } from '../../journal/services/journalApi'
import type { JournalEntry } from '../../journal/types/journal'
import { moodOptions } from '../../journal/types/journal'

export function DashboardPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [health, setHealth] = useState<HealthSummary | null>(null)
  const [journal, setJournal] = useState<JournalEntry | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const now = new Date()
        const today = format(now, 'yyyy-MM-dd')
        const [nextAccounts, nextTransactions, nextSchedules, nextHealth, todayEntries] = await Promise.all([
          financeApi.getAccounts(), financeApi.getTransactions(),
          calendarApi.getSchedules({ start: startOfDay(now).toISOString(), end: addDays(endOfDay(now), 7).toISOString() }),
          healthApi.getSummary(today), journalApi.getEntries({ start_date: today, end_date: today }),
        ])
        setAccounts(nextAccounts); setTransactions(nextTransactions); setSchedules(nextSchedules); setHealth(nextHealth); setJournal(todayEntries[0] ?? null)
      } catch (err) { setError(getApiError(err)) } finally { setLoading(false) }
    }
    void load()
  }, [])

  const now = new Date()
  const today = format(now, 'yyyy-MM-dd')
  const todayExpense = transactions.filter((item) => item.type === 'EXPENSE' && item.transaction_date === today).reduce((sum, item) => sum + Number(item.amount), 0)
  const monthExpense = transactions.filter((item) => item.type === 'EXPENSE' && item.transaction_date.startsWith(today.slice(0, 7))).reduce((sum, item) => sum + Number(item.amount), 0)
  const balance = accounts.reduce((sum, item) => sum + Number(item.current_balance), 0)
  const todaySchedules = schedules.filter((item) => item.start_datetime.startsWith(today)).sort((a, b) => a.start_datetime.localeCompare(b.start_datetime))
  const upcoming = schedules.filter((item) => isAfter(new Date(item.start_datetime), now)).sort((a, b) => a.start_datetime.localeCompare(b.start_datetime))[0]
  const mood = journal ? moodOptions.find((item) => item.value === journal.mood) : null
  const greeting = now.getHours() < 11 ? 'Chào buổi sáng' : now.getHours() < 18 ? 'Chào buổi chiều' : 'Chào buổi tối'

  if (loading) return <div className="page-content"><div className="card flex min-h-[360px] items-center justify-center text-sm text-slate-400">Đang tải tổng quan…</div></div>
  if (error) return <div className="page-content"><div className="card flex min-h-[360px] items-center justify-center text-sm text-slate-500">{error}</div></div>

  return <div className="page-content dashboard-page">
    <section className="dashboard-welcome mb-5 flex flex-wrap items-center justify-between gap-5 px-6 py-5 md:px-8 md:py-6">
      <div className="relative z-10"><h1 className="text-xs font-bold uppercase tracking-[.12em] text-blue-600">Tổng quan</h1><p className="mt-1 text-[11px] font-medium text-slate-500">{format(now, 'EEEE, dd MMMM yyyy', { locale: vi })}</p><h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-800">{greeting}</h2><p className="mt-1 text-sm text-slate-500">{upcoming ? <>Tiếp theo · <strong className="font-semibold text-slate-700">{upcoming.title}</strong> lúc {format(new Date(upcoming.start_datetime), 'HH:mm')}</> : todaySchedules.length ? `Bạn có ${todaySchedules.length} lịch trình hôm nay.` : 'Một nhịp sống gọn gàng bắt đầu từ hôm nay.'}</p></div>
      <div className="relative z-10 flex gap-2"><Link className="button-secondary" to="/calendar"><CalendarDays size={16} /> Lịch trình</Link><Link className="button-primary" to="/finance?quickAdd=transaction"><Plus size={16} /> Giao dịch</Link></div>
    </section>

    <div className="dashboard-grid">
      <section className="card dashboard-schedule overflow-hidden">
        <div className="section-heading"><div><span className="section-kicker">HÔM NAY</span><h3>Lịch trình</h3></div><Link to="/calendar" className="section-link">Mở lịch <ChevronRight size={14} /></Link></div>
        {todaySchedules.length === 0 ? <div className="empty-inline"><CalendarDays size={20} /><p>Hôm nay chưa có lịch trình.</p><Link to="/calendar?quickAdd=schedule">Lên lịch mới</Link></div> : <div className="schedule-list">{todaySchedules.slice(0, 7).map((item) => <div className="schedule-row" key={item.id}><span className="schedule-time">{format(new Date(item.start_datetime), 'HH:mm')}</span><span className="schedule-rail" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-700">{item.title}</p><p className="mt-1 text-xs text-slate-400">{format(new Date(item.start_datetime), 'HH:mm')} – {format(new Date(item.end_datetime), 'HH:mm')}{item.completed ? ' · Đã hoàn thành' : ''}</p></div>{item.completed && <span className="status-dot" title="Đã hoàn thành" />}</div>)}</div>}
        {upcoming && <div className="next-event"><span className="next-event-icon"><Clock3 size={16} /></span><div><small>SẮP TỚI</small><p>{upcoming.title}</p><span>{format(new Date(upcoming.start_datetime), 'EEEE, dd/MM · HH:mm', { locale: vi })}</span></div></div>}
      </section>

      <section className="card dashboard-finance p-5 md:p-6">
        <div className="section-heading !mb-5"><div><span className="section-kicker">TÀI CHÍNH</span><h3>Tổng quan</h3></div><Link to="/finance" className="section-link">Chi tiết <ChevronRight size={14} /></Link></div>
        <p className="text-xs font-medium text-slate-400">Tổng số dư</p><p className="mt-1 text-[28px] font-bold tracking-[-.04em] text-slate-800">{formatVnd(balance)}</p><p className="text-xs text-slate-400">Từ {accounts.length} tài khoản</p>
        <div className="finance-mini-stats"><div><span><ArrowDownLeft size={14} /> Chi hôm nay</span><strong>{formatVnd(todayExpense)}</strong></div><div><span><ArrowUpRight size={14} /> Chi tháng này</span><strong>{formatVnd(monthExpense)}</strong></div></div>
        <Link to="/finance?quickAdd=transaction" className="finance-add"><Plus size={15} /> Thêm giao dịch</Link>
      </section>

      <section className="card dashboard-health p-5 md:p-6">
        <div className="section-heading"><div><span className="section-kicker">SỨC KHỎE</span><h3>Hôm nay</h3></div><Link to="/health" className="section-link">Chi tiết <ChevronRight size={14} /></Link></div>
        {health?.profile ? <div className="health-quick-grid"><QuickMetric icon={<Activity size={16} />} label="BMI" value={health.metrics?.bmi ?? '—'} /><QuickMetric icon={<Sparkles size={16} />} label="Năng lượng" value={`${health.nutrition.calories}${health.metrics ? ` / ${Math.round(Number(health.metrics.target_calories))}` : ''} kcal`} /><QuickMetric icon={<Droplets size={16} />} label="Nước" value={health.today?.water_ml != null ? `${health.today.water_ml} ml` : 'Chưa ghi'} /><QuickMetric icon={<Moon size={16} />} label="Giấc ngủ" value={health.today?.sleep_hours != null ? `${health.today.sleep_hours} giờ` : 'Chưa ghi'} /></div> : <div className="empty-inline compact"><Activity size={20} /><p>Chưa có hồ sơ sức khỏe.</p><Link to="/health">Thêm hồ sơ</Link></div>}
      </section>

      <section className="card dashboard-journal p-5 md:p-6">
        <div className="section-heading"><div><span className="section-kicker">GHI CHÚ CỦA BẠN</span><h3>Nhật ký hôm nay</h3></div><Link to="/journal" className="section-link">Mở nhật ký <ChevronRight size={14} /></Link></div>
        {journal ? <div className="journal-preview"><div className="mood-chip"><span>{mood?.emoji}</span><strong>{mood?.label}</strong></div><p>{journal.content || 'Bạn đã lưu cảm xúc cho hôm nay.'}</p></div> : <div className="empty-inline compact"><BookOpen size={20} /><p>Chưa có ghi chú hôm nay.</p><Link to="/journal?quickAdd=journal">Viết vài dòng</Link></div>}
      </section>
    </div>
    <div className="dashboard-footnote"><WalletCards size={14} /> Số liệu được lấy từ dữ liệu cục bộ của bạn.</div>
  </div>
}

function QuickMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) { return <div className="health-quick-item"><span>{icon}</span><div><small>{label}</small><strong>{value}</strong></div></div> }
