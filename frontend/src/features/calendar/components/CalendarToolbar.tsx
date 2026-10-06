import { CalendarRange, ChevronLeft, ChevronRight } from 'lucide-react'

export function CalendarToolbar({
  label,
  onPrevious,
  onToday,
  onNext,
}: {
  label: string
  onPrevious: () => void
  onToday: () => void
  onNext: () => void
}) {
  return <div className="calendar-toolbar">
    <div className="calendar-navigation">
      <button className="calendar-nav-button" onClick={onPrevious} aria-label="Tuần trước"><ChevronLeft size={20} /></button>
      <button className="calendar-today-button" onClick={onToday}><CalendarRange size={17} /> Hôm nay</button>
      <button className="calendar-nav-button" onClick={onNext} aria-label="Tuần sau"><ChevronRight size={20} /></button>
    </div>
    <h1>{label}</h1>
    <p>Nhấn vào một khung giờ để thêm lịch trình</p>
  </div>
}
