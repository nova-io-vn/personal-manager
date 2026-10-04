import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'

export function CalendarToolbar({ label, onPrevious, onToday, onNext, onCreate }: { label: string; onPrevious: () => void; onToday: () => void; onNext: () => void; onCreate: () => void }) {
  return <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><button className="button-secondary px-2.5" onClick={onPrevious} aria-label="Tuần trước"><ChevronLeft size={17} /></button><button className="button-secondary" onClick={onToday}>Hôm nay</button><button className="button-secondary px-2.5" onClick={onNext} aria-label="Tuần sau"><ChevronRight size={17} /></button><h2 className="ml-2 text-lg font-bold text-slate-800">{label}</h2></div><button className="button-primary" onClick={onCreate}><Plus size={16} /> Lịch trình mới</button></div>
}
