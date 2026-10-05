import { addDays, differenceInMinutes, format, isSameDay, startOfDay } from 'date-fns'
import { vi } from 'date-fns/locale'
import { useEffect, useState } from 'react'
import { AlertCircle, Check, Circle, CircleCheck } from 'lucide-react'
import type { Schedule, ScheduleCategory } from '../types/calendar'
import { parseApiDateTime } from '../../../utils/dateTime'

const HOUR_HEIGHT = 76
const DAY_HEIGHT = HOUR_HEIGHT * 24

type TaskState = 'UPCOMING' | 'IN_PROGRESS' | 'OVERDUE' | 'COMPLETED'

function getTaskState(item: Schedule, now: Date): TaskState {
  if (item.completed) return 'COMPLETED'
  const start = parseApiDateTime(item.start_datetime)
  const end = parseApiDateTime(item.end_datetime)
  if (now > end) return 'OVERDUE'
  if (now >= start && now <= end) return 'IN_PROGRESS'
  return 'UPCOMING'
}

export function WeekCalendar({
  weekStart,
  schedules,
  categories,
  now,
  onSlotClick,
  onEventClick,
  onToggleComplete,
}: {
  weekStart: Date
  schedules: Schedule[]
  categories: ScheduleCategory[]
  now: Date
  onSlotClick: (date: Date) => void
  onEventClick: (item: Schedule) => void
  onToggleComplete: (item: Schedule, completed: boolean) => void
}) {
  const days = Array.from({ length: 7 }, (_, index) => addDays(weekStart, index))
  const [compact, setCompact] = useState(() => window.matchMedia('(max-width: 900px)').matches)
  const [selectedDay, setSelectedDay] = useState(() => Math.max(0, days.findIndex((day) => isSameDay(day, new Date()))))
  useEffect(() => {
    const media = window.matchMedia('(max-width: 900px)')
    const onChange = (event: MediaQueryListEvent) => setCompact(event.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])
  const visibleDays = compact ? [days[selectedDay] ?? days[0]] : days
  const gridColumns = compact ? 'grid-cols-[64px_minmax(0,1fr)]' : 'grid-cols-[76px_repeat(7,minmax(125px,1fr))]'
  const todayIsVisible = days.some((day) => isSameDay(day, now))
  const categoryMap = new Map(categories.map((item) => [item.id, item]))

  return (
    <div className="calendar-scroll card">
      <div className={compact ? 'min-w-0' : 'min-w-[980px]'}>
        {compact && <div className="grid grid-cols-4 gap-2 border-b border-slate-100 p-3 sm:grid-cols-7">{days.map((day, index) => <button type="button" key={format(day, 'yyyy-MM-dd')} className={`min-h-11 rounded-lg px-2 text-xs font-semibold ${selectedDay === index ? 'bg-blue-600 text-white' : 'bg-slate-50 text-slate-600'}`} onClick={() => setSelectedDay(index)}>{format(day, 'EEE dd', { locale: vi })}</button>)}</div>}
        <div className={`grid ${gridColumns} border-b border-slate-200 bg-white`}>
          <div />
          <div className={`${compact ? 'col-span-1' : 'col-span-7'} grid`} style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(0, 1fr))` }}>
            {visibleDays.map((day) => {
              const today = isSameDay(day, now)
              return (
                <div className={`border-l border-slate-200/80 px-2 py-3.5 text-center ${today ? 'bg-blue-50/75' : ''}`} key={format(day, 'yyyy-MM-dd')}>
                  <p className={`text-xs font-extrabold uppercase tracking-wide ${today ? 'text-blue-700' : 'text-slate-500'}`}>{format(day, 'EEEE', { locale: vi })}</p>
                  <p className={`mx-auto mt-1 grid size-9 place-items-center rounded-full text-xl font-extrabold ${today ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-800'}`}>{format(day, 'dd')}</p>
                </div>
              )
            })}
          </div>
        </div>

        <div className={`grid ${gridColumns}`}>
          <div className="relative" style={{ height: DAY_HEIGHT }}>
            {Array.from({ length: 25 }, (_, hour) => (
              <span className="absolute right-3 text-xs font-semibold tabular-nums text-slate-500" style={{ top: hour * HOUR_HEIGHT - 8 }} key={hour}>
                {String(hour).padStart(2, '0')}:00
              </span>
            ))}
          </div>

          <div className={`${compact ? 'col-span-1' : 'col-span-7'} grid`} style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(0, 1fr))` }}>
            {visibleDays.map((day) => {
              const today = isSameDay(day, now)
              return (
                <div
                  className={`relative border-l border-slate-100 ${today ? 'calendar-today-column' : ''}`}
                  style={{ height: DAY_HEIGHT }}
                  key={format(day, 'yyyy-MM-dd')}
                  onClick={(event) => {
                    if (event.target !== event.currentTarget) return
                    const rect = event.currentTarget.getBoundingClientRect()
                    const minutes = Math.max(0, Math.min(1439, Math.floor(((event.clientY - rect.top) / HOUR_HEIGHT) * 60)))
                    const slot = new Date(day)
                    slot.setHours(Math.floor(minutes / 60), minutes % 60, 0, 0)
                    onSlotClick(slot)
                  }}
                >
                  {Array.from({ length: 25 }, (_, hour) => <div className="pointer-events-none absolute inset-x-0 border-t border-slate-100" style={{ top: hour * HOUR_HEIGHT }} key={hour} />)}
                  {today && todayIsVisible && <div className="current-time-line" style={{ top: ((now.getHours() * 60 + now.getMinutes()) / 60) * HOUR_HEIGHT }}><span>{format(now, 'HH:mm')}</span></div>}
                  {schedules.filter((item) => {
                    const start = parseApiDateTime(item.start_datetime)
                    const end = parseApiDateTime(item.end_datetime)
                    return isSameDay(start, day) || (start < day && end > startOfDay(day))
                  }).map((item) => {
                    const start = parseApiDateTime(item.start_datetime)
                    const end = parseApiDateTime(item.end_datetime)
                    const dayStart = startOfDay(day)
                    const top = Math.max(0, differenceInMinutes(start, dayStart))
                    const bottom = Math.min(1440, differenceInMinutes(end, dayStart))
                    const category = item.category_id ? categoryMap.get(item.category_id) : undefined
                    const color = item.color || category?.color || '#2563eb'
                    const state = getTaskState(item, now)
                    const stateStyles = {
                      UPCOMING: { backgroundColor: `${color}18`, borderColor: color, label: '', icon: null, text: color },
                      IN_PROGRESS: { backgroundColor: '#eff6ff', borderColor: '#2563eb', label: 'Đang diễn ra', icon: <Circle size={12} />, text: '#1d4ed8' },
                      OVERDUE: { backgroundColor: '#fff1f2', borderColor: '#e11d48', label: 'Quá hạn', icon: <AlertCircle size={12} />, text: '#be123c' },
                      COMPLETED: { backgroundColor: '#f1f5f9', borderColor: '#94a3b8', label: 'Đã xong', icon: <CircleCheck size={12} />, text: '#64748b' },
                    }[state]

                    return (
                      <div
                        className={`absolute inset-x-1 z-10 flex overflow-hidden rounded-md border-l-4 shadow-sm transition-colors ${state === 'COMPLETED' ? 'opacity-75' : ''}`}
                        style={{ top: (top / 60) * HOUR_HEIGHT, height: Math.max(((bottom - top) / 60) * HOUR_HEIGHT, 32), backgroundColor: stateStyles.backgroundColor, borderLeftColor: stateStyles.borderColor }}
                        key={`${item.id}-${item.start_datetime}`}
                      >
                        <button
                          type="button"
                          className="grid min-h-11 w-9 shrink-0 place-items-center text-slate-500 hover:bg-black/5"
                          aria-label={`${item.completed ? 'Bỏ hoàn thành' : 'Đánh dấu hoàn thành'}: ${item.title}`}
                          title={item.completed ? 'Bỏ hoàn thành' : 'Đánh dấu hoàn thành'}
                          onClick={() => onToggleComplete(item, !item.completed)}
                        >
                          {item.completed ? <Check size={15} className="text-slate-500" /> : <Circle size={15} />}
                        </button>
                        <button type="button" className="min-w-0 flex-1 overflow-hidden px-1.5 py-1.5 text-left" onClick={() => onEventClick(item)}>
                          <p className={`truncate text-[13px] font-extrabold leading-5 ${state === 'COMPLETED' ? 'text-slate-500 line-through' : ''}`} style={{ color: state === 'UPCOMING' ? color : stateStyles.text }}>{item.title}</p>
                          <p className="truncate text-[11px] font-semibold tabular-nums text-slate-600">{format(start, 'HH:mm')} – {format(end, 'HH:mm')}</p>
                          {stateStyles.label && <p className="mt-0.5 flex items-center gap-1 truncate text-[10px] font-semibold" style={{ color: stateStyles.text }}>{stateStyles.icon}{stateStyles.label}</p>}
                        </button>
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
