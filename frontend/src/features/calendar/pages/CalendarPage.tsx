import { useCallback, useEffect, useState } from 'react'
import { addWeeks, endOfWeek, format, startOfWeek } from 'date-fns'
import { vi } from 'date-fns/locale'
import { RefreshCw } from 'lucide-react'
import { getApiError } from '../../../services/api'
import { CalendarToolbar } from '../components/CalendarToolbar'
import { ScheduleForm } from '../components/ScheduleForm'
import { WeekCalendar } from '../components/WeekCalendar'
import { calendarApi } from '../services/calendarApi'
import type { Schedule, ScheduleCategory } from '../types/calendar'
import { settingsApi } from '../../settings/services/settingsApi'
import { useLocation, useNavigate } from 'react-router-dom'

export function CalendarPage() {
  const location = useLocation(); const navigate = useNavigate()
  const [week, setWeek] = useState(() => startOfWeek(new Date(), { weekStartsOn: 1 })); const [categories, setCategories] = useState<ScheduleCategory[]>([]); const [schedules, setSchedules] = useState<Schedule[]>([]); const [defaultReminderMinutes, setDefaultReminderMinutes] = useState(0); const [selected, setSelected] = useState<Schedule | null | false>(false); const [slotDate, setSlotDate] = useState(new Date()); const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const loadData = useCallback(async () => { setLoading(true); setError(''); try { const start = startOfWeek(week, { weekStartsOn: 1 }); const end = endOfWeek(week, { weekStartsOn: 1 }); const [nextCategories, nextSchedules, appSettings] = await Promise.all([calendarApi.getCategories(), calendarApi.getSchedules({ start: start.toISOString(), end: end.toISOString() }), settingsApi.get()]); setCategories(nextCategories); setSchedules(nextSchedules); setDefaultReminderMinutes(appSettings.default_reminder_minutes) } catch (err) { setError(getApiError(err)) } finally { setLoading(false) } }, [week])
  // The effect synchronizes the selected week with the server.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void loadData() }, [loadData])
  // Consume the one-shot action encoded by the Quick Add navigation.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (new URLSearchParams(location.search).get('quickAdd') === 'schedule') { setSlotDate(new Date()); setSelected(null); navigate('/calendar', { replace: true }) } }, [location.search, navigate])
  const submit = async (payload: Record<string, unknown>, id?: number) => { setBusy(true); try { if (id) await calendarApi.updateSchedule(id, payload); else await calendarApi.createSchedule(payload); setSelected(false); await loadData() } catch (err) { setError(getApiError(err)) } finally { setBusy(false) } }
  const remove = async (item: Schedule) => { if (!window.confirm(`Xóa lịch trình “${item.title}”?`)) return; setBusy(true); try { await calendarApi.deleteSchedule(item.id); setSelected(false); await loadData() } catch (err) { setError(getApiError(err)) } finally { setBusy(false) } }
  const label = `${format(week, 'dd/MM', { locale: vi })} – ${format(endOfWeek(week, { weekStartsOn: 1 }), 'dd/MM/yyyy', { locale: vi })}`
  const openEvent = async (item: Schedule) => { setSlotDate(new Date(item.start_datetime)); if (!item.is_recurring_occurrence) { setSelected(item); return } try { setSelected(await calendarApi.getSchedule(item.id)) } catch (err) { setError(getApiError(err)) } }
  return <div className="page-content"><div className="mb-6"><p className="text-sm font-semibold text-blue-600">Tuần làm việc của bạn</p><h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-800">Lịch trình</h2><p className="mt-1 text-sm text-slate-500">Lên kế hoạch từ thứ Hai đến Chủ nhật, theo từng khung giờ.</p></div><CalendarToolbar label={label} onPrevious={() => setWeek((value) => addWeeks(value, -1))} onToday={() => setWeek(startOfWeek(new Date(), { weekStartsOn: 1 }))} onNext={() => setWeek((value) => addWeeks(value, 1))} onCreate={() => { setSlotDate(new Date()); setSelected(null) }} />{error && <div className="mb-4 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"><span>{error}</span><button onClick={() => void loadData()} className="font-bold underline"><RefreshCw size={14} /></button></div>}{loading ? <div className="card flex min-h-[500px] items-center justify-center text-sm text-slate-400">Đang tải lịch trình…</div> : <WeekCalendar weekStart={week} schedules={schedules} categories={categories} onSlotClick={(date) => { setSlotDate(date); setSelected(null) }} onEventClick={(item) => void openEvent(item)} />}{selected !== false && <ScheduleForm categories={categories} editing={selected} initialDate={slotDate} defaultReminderMinutes={defaultReminderMinutes} onClose={() => setSelected(false)} onSubmit={submit} onDelete={remove} busy={busy} />}</div>
}
