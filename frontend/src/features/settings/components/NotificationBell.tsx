import { useCallback, useEffect, useRef, useState } from 'react'
import { Bell, BookOpen, CalendarDays, Check, ClipboardList, HeartPulse, WalletCards } from 'lucide-react'
import { format } from 'date-fns'
import { vi } from 'date-fns/locale'
import { notificationApi } from '../services/settingsApi'
import type { AppNotification } from '../types/settings'

const eventLabels: Record<AppNotification['event_type'], string> = { SCHEDULE_REMINDER: 'Lịch trình', BUDGET_WARNING: 'Ngân sách', JOURNAL_REMINDER: 'Nhật ký', HEALTH_REMINDER: 'Sức khỏe', DAILY_SUMMARY: 'Tổng kết' }
const eventIcons = { SCHEDULE_REMINDER: CalendarDays, BUDGET_WARNING: WalletCards, JOURNAL_REMINDER: BookOpen, HEALTH_REMINDER: HeartPulse, DAILY_SUMMARY: ClipboardList }

export function NotificationBell() {
  const [open, setOpen] = useState(false); const [items, setItems] = useState<AppNotification[]>([]); const [error, setError] = useState(''); const wrapper = useRef<HTMLDivElement>(null)
  const load = useCallback(async () => { try { setItems(await notificationApi.list({ limit: 20 })); setError('') } catch { setError('Không thể tải thông báo.') } }, [])
  // Load persisted notifications when the shared application shell mounts.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load() }, [load])
  useEffect(() => { const close = (event: MouseEvent) => { if (wrapper.current && !wrapper.current.contains(event.target as Node)) setOpen(false) }; document.addEventListener('mousedown', close); return () => document.removeEventListener('mousedown', close) }, [])
  const unread = items.filter((item) => !item.read_at).length
  const markRead = async (item: AppNotification) => { if (item.read_at) return; try { const updated = await notificationApi.markRead(item.id); setItems((value) => value.map((current) => current.id === item.id ? updated : current)) } catch { setError('Không thể đánh dấu đã đọc.') } }
  return <div className="relative" ref={wrapper}><button className="icon-button relative" aria-label="Thông báo" aria-expanded={open} onClick={() => { setOpen((value) => !value); if (!open) void load() }}><Bell size={18} />{unread > 0 && <span className="absolute right-0.5 top-0.5 min-w-4 rounded-full bg-blue-600 px-1 text-center text-[9px] font-bold leading-4 text-white">{Math.min(unread, 99)}</span>}</button>{open && <div className="notification-panel"><div className="flex items-center justify-between border-b border-slate-100 px-4 py-3.5"><div><h3 className="text-sm font-bold text-slate-800">Thông báo</h3><p className="text-[11px] text-slate-400">{unread ? `${unread} chưa đọc` : 'Bạn đã đọc tất cả'}</p></div><span className="text-[10px] text-slate-400">20 gần nhất</span></div>{error && <p className="bg-amber-50 px-4 py-2 text-xs text-amber-700">{error}</p>}<div className="max-h-[430px] overflow-auto">{items.length === 0 ? <div className="px-5 py-10 text-center text-sm text-slate-400">Chưa có thông báo.</div> : items.map((item) => { const Icon = eventIcons[item.event_type]; return <button type="button" key={item.id} className={`block w-full border-b border-slate-100 px-4 py-3 text-left hover:bg-slate-50 ${item.read_at ? '' : 'bg-blue-50/55'}`} onClick={() => void markRead(item)}><div className="flex items-start gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-[10px] bg-blue-50 text-blue-600"><Icon size={15} /></span><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-bold text-slate-700">{item.title}</p>{item.read_at && <Check size={13} className="text-emerald-500" />}</div><p className="mt-1 whitespace-pre-line text-xs leading-5 text-slate-500">{item.message}</p><p className="mt-2 text-[10px] text-slate-400">{eventLabels[item.event_type]} · {item.channel === 'LOCAL' ? 'Trong ứng dụng' : 'Telegram'} · {format(new Date(item.created_at), 'dd/MM HH:mm', { locale: vi })}</p>{item.status === 'FAILED' && <span className="mt-1 inline-block text-[10px] font-bold text-rose-600">Gửi thất bại</span>}</div></div></button>})}</div></div>}</div>
}
