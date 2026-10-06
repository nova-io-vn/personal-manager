import { useCallback, useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { CalendarDays, Plus, Save, Trash2 } from 'lucide-react'
import { getApiError } from '../../../services/api'
import { DrawingCanvasWithJournalHeading as DrawingCanvas } from '../components/DrawingCanvasWithJournalHeading'
import { journalApi } from '../services/journalApi'
import type { JournalEntry, JournalTag, Mood } from '../types/journal'
import { moodOptions } from '../types/journal'

export function JournalPage() {
  const today = format(new Date(), 'yyyy-MM-dd')
  const [selectedDate, setSelectedDate] = useState(today)
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [tags, setTags] = useState<JournalTag[]>([])
  const [mood, setMood] = useState<Mood>('NEUTRAL')
  const [drawing, setDrawing] = useState<string | null>(null)
  const [selectedTags, setSelectedTags] = useState<number[]>([])
  const [newTag, setNewTag] = useState('')
  const [filterMood, setFilterMood] = useState<Mood | ''>('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const applyEntry = (date: string, source: JournalEntry[]) => {
    setSelectedDate(date)
    const entry = source.find((item) => item.entry_date === date)
    setMood(entry?.mood ?? 'NEUTRAL')
    setDrawing(entry?.drawing_data ?? null)
    setSelectedTags(entry?.tags.map((tag) => tag.id) ?? [])
  }
  const loadData = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const [nextEntries, nextTags] = await Promise.all([journalApi.getEntries(), journalApi.getTags()])
      setEntries(nextEntries); setTags(nextTags); applyEntry(selectedDate, nextEntries)
    } catch (err) { setError(getApiError(err)) } finally { setLoading(false) }
  }, [selectedDate])
  // Load the selected journal snapshot when the screen opens.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void loadData() }, [loadData])

  const current = entries.find((item) => item.entry_date === selectedDate)
  const filteredEntries = useMemo(() => filterMood ? entries.filter((item) => item.mood === filterMood) : entries, [entries, filterMood])
  const save = async () => {
    setBusy(true); setError('')
    try {
      await journalApi.saveEntry(selectedDate, { mood, content: current?.content ?? '', drawing_data: drawing, tag_ids: selectedTags })
      await loadData()
    } catch (err) { setError(getApiError(err)) } finally { setBusy(false) }
  }
  const remove = async () => {
    if (!current || !window.confirm('Xóa nhật ký ngày này?')) return
    setBusy(true)
    try {
      await journalApi.deleteEntry(selectedDate)
      const nextEntries = await journalApi.getEntries(); setEntries(nextEntries); applyEntry(selectedDate, nextEntries)
    } catch (err) { setError(getApiError(err)) } finally { setBusy(false) }
  }
  const createTag = async () => {
    if (!newTag.trim()) return
    setBusy(true)
    try {
      const tag = await journalApi.createTag(newTag); setTags((value) => [...value, tag]); setSelectedTags((value) => [...value, tag.id]); setNewTag('')
    } catch (err) { setError(getApiError(err)) } finally { setBusy(false) }
  }

  if (loading && !entries.length) return <div className="page-content"><div className="card empty-state">Đang tải nhật ký…</div></div>
  return <div className="page-content journal-page">
    <div className="page-heading-row journal-heading">
      <div><p className="eyebrow">Không gian sáng tạo mỗi ngày</p><h1>Nhật ký hình ảnh</h1><p className="page-subtitle">Vẽ tự do bằng chuột, bút cảm ứng hoặc ngón tay trên tablet.</p></div>
      <label className="journal-date-picker"><CalendarDays size={17} /><input type="date" value={selectedDate} onChange={(event) => applyEntry(event.target.value, entries)} /></label>
    </div>
    {error && <div className="notice notice-error">{error}</div>}
    <div className="journal-workspace">
      <section className="card journal-canvas-panel">
        <div className="journal-editor-head">
          <div><h3>{selectedDate === today ? 'Hôm nay' : selectedDate}</h3><p>Chọn tâm trạng rồi ghi lại ngày của bạn bằng nét vẽ.</p></div>
          {current && <span className="status-badge">Đã lưu</span>}
        </div>
        <div className="journal-mood-strip">{moodOptions.map((option) => <button type="button" key={option.value} className={`mood-button${mood === option.value ? ' is-selected' : ''}`} onClick={() => setMood(option.value)}><span>{option.emoji}</span><small>{option.label}</small></button>)}</div>
        <DrawingCanvas key={selectedDate} value={drawing} onChange={setDrawing} />
        <div className="journal-savebar">
          {current ? <button className="danger-text" onClick={() => void remove()}><Trash2 size={15} /> Xóa</button> : <span />}
          <button className="button-primary" disabled={busy} onClick={() => void save()}><Save size={16} /> {busy ? 'Đang lưu…' : 'Lưu trang nhật ký'}</button>
        </div>
      </section>

      <aside className="journal-side-panel">
        <section className="card journal-tags-panel"><h3>Nhãn</h3><p>Phân loại trang nhật ký để tìm lại nhanh hơn.</p><div className="mt-4 flex flex-wrap gap-2">{tags.map((tag) => { const selected = selectedTags.includes(tag.id); return <button type="button" key={tag.id} className={`tag-chip${selected ? ' is-selected' : ''}`} onClick={() => setSelectedTags((value) => selected ? value.filter((id) => id !== tag.id) : [...value, tag.id])}>#{tag.name}</button> })}</div><div className="mt-3 flex gap-2"><input className="field py-2 text-sm" value={newTag} onChange={(event) => setNewTag(event.target.value)} placeholder="Nhãn mới" /><button type="button" className="button-secondary py-2" disabled={busy} onClick={() => void createTag()}><Plus size={14} /></button></div></section>
        <section className="card journal-history-panel"><div className="journal-history-head"><div><h3>Lịch sử</h3><p>Chọn ngày để mở lại bản vẽ.</p></div><select className="field" value={filterMood} onChange={(event) => setFilterMood(event.target.value as Mood | '')}><option value="">Mọi tâm trạng</option>{moodOptions.map((option) => <option value={option.value} key={option.value}>{option.emoji} {option.label}</option>)}</select></div>{filteredEntries.length === 0 ? <p className="p-6 text-center text-sm text-slate-400">Chưa có trang nhật ký.</p> : <div className="journal-history-list">{filteredEntries.map((entry) => { const option = moodOptions.find((item) => item.value === entry.mood); return <button type="button" className={entry.entry_date === selectedDate ? 'is-active' : ''} key={entry.id} onClick={() => applyEntry(entry.entry_date, entries)}><span><strong>{entry.entry_date}</strong><small>{entry.drawing_data ? 'Có bản vẽ' : 'Trang trống'}</small></span><b>{option?.emoji}</b></button> })}</div>}</section>
      </aside>
    </div>
  </div>
}
