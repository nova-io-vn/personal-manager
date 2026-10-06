import { useEffect, useState } from 'react'
import { addDays, endOfDay, format, isAfter, startOfDay } from 'date-fns'
import { vi } from 'date-fns/locale'
import { Activity, AlertCircle, ArrowDownLeft, ArrowUpRight, BookOpen, CalendarDays, Check, ChevronRight, Clock3, Droplets, Moon, Plus, Sparkles, WalletCards } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getApiError } from '../../../services/api'
import { useAppClock } from '../../../stores/clockStore'
import { parseApiDateTime } from '../../../utils/dateTime'
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

type ScheduleState = 'UPCOMING' | 'IN_PROGRESS' | 'OVERDUE' | 'COMPLETED'

export function DashboardPage() {
  const now = useAppClock()
  const today = format(now, 'yyyy-MM-dd')
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
        const day = new Date(`${today}T00:00:00`)
        const [nextAccounts, nextTransactions, nextSchedules, nextHealth, todayEntries] = await Promise.all([
          financeApi.getAccounts(), financeApi.getTransactions(),
          calendarApi.getSchedules({ start: startOfDay(day).toISOString(), end: addDays(endOfDay(day), 7).toISOString() }),
          healthApi.getSummary(today), journalApi.getEntries({ start_date: today, end_date: today }),
        ])
        setAccounts(nextAccounts); setTransactions(nextTransactions); setSchedules(nextSchedules); setHealth(nextHealth); setJournal(todayEntries[0] ?? null)
      } catch (err) { setError(getApiError(err)) } finally { setLoading(false) }
    }
    void load()
  }, [today])

  const todayExpense = transactions.filter((item) => item.type === 'EXPENSE' && item.transaction_date === today).reduce((sum, item) => sum + Number(item.amount), 0)
  const monthExpense = transactions.filter((item) => item.type === 'EXPENSE' && item.transaction_date.startsWith(today.slice(0, 7))).reduce((sum, item) => sum + Number(item.amount), 0)
  const balance = accounts.reduce((sum, item) => sum + Number(item.current_balance), 0)
  const todaySchedules = schedules.filter((item) => format(parseApiDateTime(item.start_datetime), 'yyyy-MM-dd') === today).sort((a, b) => a.start_datetime.localeCompare(b.start_datetime))
  const overdueSchedules = todaySchedules.filter((item) => getScheduleState(item, now) === 'OVERDUE')
  const completedSchedules = todaySchedules.filter((item) => item.completed).length
  const upcoming = schedules.filter((item) => !item.completed && isAfter(parseApiDateTime(item.start_datetime), now)).sort((a, b) => a.start_datetime.localeCompare(b.start_datetime))[0]
  const mood = journal ? moodOptions.find((item) => item.value === journal.mood) : null
  const greeting = now.getHours() < 11 ? 'Chào buổi sáng' : now.getHours() < 18 ? 'Chào buổi chiều' : 'Chào buổi tối'
  const completion = todaySchedules.length ? Math.round((completedSchedules / todaySchedules.length) * 100) : 0

  const toggleSchedule = async (item: Schedule) => {
    try {
      const updated = await calendarApi.setOccurrenceCompleted(item.id, item.start_datetime, !item.completed)
      setSchedules((current) => current.map((schedule) => schedule.id === item.id && schedule.start_datetime === item.start_datetime ? { ...schedule, completed: updated.completed } : schedule))
    } catch (err) { setError(getApiError(err)) }
  }

  if (loading) return <div className="page-content"><div className="card empty-state">Đang tải tổng quan…</div></div>
  if (error) return <div className="page-content"><div className="notice notice-error">{error}</div></div>

  return <div className="page-content dashboard-page">
    <section className="dashboard-welcome dashboard-hero">
      <div className="dashboard-hero-copy"><p className="eyebrow">{format(now, 'EEEE, dd MMMM yyyy', { locale: vi })}</p><h1>Tổng quan</h1><h2>{greeting}</h2><p>{upcoming ? <>Lịch tiếp theo: <strong>{upcoming.title}</strong> lúc {format(parseApiDateTime(upcoming.start_datetime), 'HH:mm')}</> : todaySchedules.length ? `Bạn có ${todaySchedules.length} lịch trình hôm nay.` : 'Hôm nay đang rộng mở — hãy bắt đầu theo nhịp của bạn.'}</p></div>
      <div className="dashboard-hero-progress"><div className="hero-progress-ring" style={{ '--progress': `${completion * 3.6}deg` } as React.CSSProperties}><span>{completedSchedules}/{todaySchedules.length}</span></div><div><strong>Hoàn thành hôm nay</strong><small>{overdueSchedules.length ? `${overdueSchedules.length} việc đang quá hạn` : 'Bạn đang theo đúng kế hoạch'}</small></div></div>
    </section>

    <div className="dashboard-grid dashboard-workspace">
      <section className="card dashboard-schedule overflow-hidden">
        <div className="section-heading"><div><span className="section-kicker">LỊCH HÔM NAY</span><h3>Nhịp ngày của bạn</h3><p>Xem thời gian, mô tả và trạng thái từng lịch trình.</p></div><Link to="/calendar" className="section-link">Mở lịch <ChevronRight size={14} /></Link></div>
        {todaySchedules.length === 0 ? <div className="empty-inline"><CalendarDays size={24} /><p>Hôm nay chưa có lịch trình.</p><Link to="/calendar">Nhấn vào khung giờ để lên lịch</Link></div> : <div className="dashboard-agenda">{todaySchedules.map((item) => <ScheduleRow key={`${item.id}-${item.start_datetime}`} item={item} now={now} onToggle={() => void toggleSchedule(item)} />)}</div>}
        {upcoming && <div className="next-event"><span className="next-event-icon"><Clock3 size={16} /></span><div><small>SẮP TỚI</small><p>{upcoming.title}</p><span>{format(parseApiDateTime(upcoming.start_datetime), 'EEEE, dd/MM · HH:mm', { locale: vi })}{upcoming.description ? ` · ${upcoming.description}` : ''}</span></div></div>}
      </section>

      <section className="card dashboard-finance dashboard-accent-card p-5 md:p-6">
        <div className="section-heading"><div><span className="section-kicker">TÀI CHÍNH</span><h3>Dòng tiền</h3></div><Link to="/finance" className="section-link">Chi tiết <ChevronRight size={14} /></Link></div>
        <p className="text-xs font-semibold text-slate-500">Tổng số dư</p><p className="mt-1 text-[30px] font-extrabold tracking-[-.05em] text-slate-800">{formatVnd(balance)}</p><p className="text-xs text-slate-400">Từ {accounts.length} tài khoản</p>
        <div className="finance-mini-stats"><div><span><ArrowDownLeft size={14} /> Chi hôm nay</span><strong>{formatVnd(todayExpense)}</strong></div><div><span><ArrowUpRight size={14} /> Chi tháng này</span><strong>{formatVnd(monthExpense)}</strong></div></div>
        <Link to="/finance?quickAdd=transaction" className="finance-add"><Plus size={15} /> Thêm giao dịch</Link>
      </section>

      <section className="card dashboard-health p-5 md:p-6">
        <div className="section-heading"><div><span className="section-kicker">SỨC KHỎE</span><h3>Chỉ số hôm nay</h3></div><Link to="/health" className="section-link">Chi tiết <ChevronRight size={14} /></Link></div>
        {health?.profile ? <div className="health-quick-grid"><QuickMetric icon={<Activity size={16} />} label="BMI" value={health.metrics?.bmi ?? '—'} /><QuickMetric icon={<Sparkles size={16} />} label="Năng lượng" value={`${health.nutrition.calories}${health.metrics ? ` / ${Math.round(Number(health.metrics.target_calories))}` : ''} kcal`} /><QuickMetric icon={<Droplets size={16} />} label="Nước" value={health.today?.water_ml != null ? `${health.today.water_ml} ml` : 'Chưa ghi'} /><QuickMetric icon={<Moon size={16} />} label="Giấc ngủ" value={health.today?.sleep_hours != null ? `${health.today.sleep_hours} giờ` : 'Chưa ghi'} /></div> : <div className="empty-inline compact"><Activity size={20} /><p>Chưa có hồ sơ sức khỏe.</p><Link to="/health">Thêm hồ sơ</Link></div>}
      </section>

      <section className="card dashboard-journal p-5 md:p-6">
        <div className="section-heading"><div><span className="section-kicker">NHẬT KÝ</span><h3>Dấu ấn hôm nay</h3></div><Link to="/journal" className="section-link">Mở sổ vẽ <ChevronRight size={14} /></Link></div>
        {journal ? <div className="journal-preview"><div className="mood-chip"><span>{mood?.emoji}</span><strong>{mood?.label}</strong></div><p>{journal.drawing_data ? 'Bạn đã lưu một bản vẽ cho hôm nay.' : journal.content || 'Bạn đã lưu tâm trạng hôm nay.'}</p></div> : <div className="empty-inline compact"><BookOpen size={20} /><p>Chưa có trang nhật ký hôm nay.</p><Link to="/journal">Mở bảng vẽ</Link></div>}
      </section>
    </div>
    <div className="dashboard-footnote"><WalletCards size={14} /> Tất cả số liệu được lấy từ dữ liệu thật của bạn.</div>
  </div>
}

function ScheduleRow({ item, now, onToggle }: { item: Schedule; now: Date; onToggle: () => void }) {
  const state = getScheduleState(item, now)
  const labels: Record<ScheduleState, string> = { UPCOMING: 'Sắp tới', IN_PROGRESS: 'Đang diễn ra', OVERDUE: 'Quá hạn', COMPLETED: 'Đã xong' }
  const start = parseApiDateTime(item.start_datetime); const end = parseApiDateTime(item.end_datetime)
  return <article className={`dashboard-agenda-row state-${state.toLowerCase()}`}>
    <div className="agenda-time"><strong>{format(start, 'HH:mm')}</strong><span>{format(end, 'HH:mm')}</span></div>
    <button type="button" className="agenda-check" aria-label={`${item.completed ? 'Bỏ hoàn thành' : 'Đánh dấu hoàn thành'}: ${item.title}`} onClick={onToggle}>{item.completed ? <Check size={16} /> : state === 'OVERDUE' ? <AlertCircle size={16} /> : <span />}</button>
    <div className="agenda-copy"><div><h4>{item.title}</h4><span className="agenda-status">{labels[state]}</span></div>{item.description && <p>{item.description}</p>}</div>
  </article>
}

function QuickMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) { return <div className="health-quick-item"><span>{icon}</span><div><small>{label}</small><strong>{value}</strong></div></div> }

function getScheduleState(item: Schedule, now: Date): ScheduleState {
  if (item.completed) return 'COMPLETED'
  const start = parseApiDateTime(item.start_datetime); const end = parseApiDateTime(item.end_datetime)
  if (now > end) return 'OVERDUE'
  if (now >= start && now <= end) return 'IN_PROGRESS'
  return 'UPCOMING'
}
