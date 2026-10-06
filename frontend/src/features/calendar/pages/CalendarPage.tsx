import { useCallback, useEffect, useRef, useState } from 'react'
import { addWeeks, endOfWeek, format, isSameDay, isSameWeek, startOfWeek } from 'date-fns'
import { vi } from 'date-fns/locale'
import { RefreshCw } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { getApiError } from '../../../services/api'
import { useAppClock } from '../../../stores/clockStore'
import { parseApiDateTime } from '../../../utils/dateTime'
import { CalendarToolbar } from '../components/CalendarToolbar'
import { ScheduleForm } from '../components/ScheduleForm'
import { WeekCalendar } from '../components/WeekCalendar'
import { calendarApi } from '../services/calendarApi'
import type { Schedule, ScheduleCategory } from '../types/calendar'
import { settingsApi } from '../../settings/services/settingsApi'

export function CalendarPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const now = useAppClock()
  const [week, setWeek] = useState(() => startOfWeek(new Date(), { weekStartsOn: 1 }))
  const previousClockValue = useRef(now)
  const [categories, setCategories] = useState<ScheduleCategory[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [defaultReminderMinutes, setDefaultReminderMinutes] = useState(0)
  const [selected, setSelected] = useState<Schedule | null | false>(false)
  const [slotDate, setSlotDate] = useState(new Date())
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const start = startOfWeek(week, { weekStartsOn: 1 })
      const end = endOfWeek(week, { weekStartsOn: 1 })
      const [nextCategories, nextSchedules, appSettings] = await Promise.all([
        calendarApi.getCategories(),
        calendarApi.getSchedules({ start: start.toISOString(), end: end.toISOString() }),
        settingsApi.get(),
      ])
      setCategories(nextCategories)
      setSchedules(nextSchedules)
      setDefaultReminderMinutes(appSettings.default_reminder_minutes)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }, [week])

  // Fetching route data is the intended synchronization side effect.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void loadData() }, [loadData])

  // If this week was the current week before midnight, follow the new local day.
  useEffect(() => {
    const previous = previousClockValue.current
    if (!isSameDay(previous, now) && isSameWeek(week, previous, { weekStartsOn: 1 })) {
      setWeek(startOfWeek(now, { weekStartsOn: 1 }))
    }
    previousClockValue.current = now
  }, [now, week])

  // Consume a route action once and open the existing schedule form.
  useEffect(() => {
    if (new URLSearchParams(location.search).get('quickAdd') === 'schedule') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSlotDate(now)
      setSelected(null)
      navigate('/calendar', { replace: true })
    }
  }, [location.search, navigate, now])

  const submit = async (payload: Record<string, unknown>, id?: number) => {
    setBusy(true)
    try {
      if (id) await calendarApi.updateSchedule(id, payload)
      else await calendarApi.createSchedule(payload)
      setSelected(false)
      await loadData()
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setBusy(false)
    }
  }

  const remove = async (item: Schedule) => {
    if (!window.confirm(`Xóa lịch trình “${item.title}”?`)) return
    setBusy(true)
    try {
      await calendarApi.deleteSchedule(item.id)
      setSelected(false)
      await loadData()
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setBusy(false)
    }
  }

  const toggleComplete = async (item: Schedule, completed: boolean) => {
    setBusy(true)
    setError('')
    try {
      const updated = await calendarApi.setOccurrenceCompleted(item.id, item.start_datetime, completed)
      setSchedules((current) => current.map((schedule) => (
        schedule.id === item.id && schedule.start_datetime === item.start_datetime
          ? { ...schedule, completed: updated.completed }
          : schedule
      )))
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setBusy(false)
    }
  }

  const label = `${format(week, 'dd MMM', { locale: vi })} – ${format(endOfWeek(week, { weekStartsOn: 1 }), 'dd MMM yyyy', { locale: vi })}`
  const openEvent = async (item: Schedule) => {
    setSlotDate(parseApiDateTime(item.start_datetime))
    if (!item.is_recurring_occurrence) {
      setSelected(item)
      return
    }
    try {
      setSelected(await calendarApi.getSchedule(item.id))
    } catch (err) {
      setError(getApiError(err))
    }
  }

  return (
    <div className="page-content calendar-page">
      <h2 className="sr-only">Lịch trình</h2>
      <CalendarToolbar
        label={label}
        onPrevious={() => setWeek((value) => addWeeks(value, -1))}
        onToday={() => setWeek(startOfWeek(now, { weekStartsOn: 1 }))}
        onNext={() => setWeek((value) => addWeeks(value, 1))}
      />
      {error && <div className="mb-4 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"><span>{error}</span><button aria-label="Thử tải lại" onClick={() => void loadData()} className="font-bold underline"><RefreshCw size={14} /></button></div>}
      {loading
        ? <div className="card flex min-h-[500px] items-center justify-center text-sm text-slate-400">Đang tải lịch trình…</div>
        : <WeekCalendar weekStart={week} schedules={schedules} categories={categories} now={now} onSlotClick={(date) => { setSlotDate(date); setSelected(null) }} onEventClick={(item) => void openEvent(item)} onToggleComplete={(item, completed) => void toggleComplete(item, completed)} />}
      {selected !== false && <ScheduleForm categories={categories} editing={selected} initialDate={slotDate} defaultReminderMinutes={defaultReminderMinutes} onClose={() => setSelected(false)} onSubmit={submit} onDelete={remove} busy={busy} />}
    </div>
  )
}
