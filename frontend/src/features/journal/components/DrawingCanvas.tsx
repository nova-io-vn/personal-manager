import { useEffect, useRef, useState } from 'react'
import { Eraser, Grid3X3, Highlighter, Pencil, Redo2, RotateCcw, Undo2 } from 'lucide-react'

interface Props { value: string | null; onChange: (value: string | null) => void }
type Tool = 'pen' | 'marker' | 'eraser'
const colors = ['#173b63', '#2563eb', '#dc2626', '#16a34a', '#7c3aed', '#111827']

export function DrawingCanvas({ value, onChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const drawing = useRef(false)
  const last = useRef({ x: 0, y: 0 })
  const history = useRef<string[]>([])
  const historyIndex = useRef(-1)
  const [tool, setTool] = useState<Tool>('pen')
  const [color, setColor] = useState('#173b63')
  const [size, setSize] = useState(4)
  const [grid, setGrid] = useState(true)
  const [canUndo, setCanUndo] = useState(false)
  const [canRedo, setCanRedo] = useState(false)

  const paintWhite = (canvas: HTMLCanvasElement) => {
    const context = canvas.getContext('2d')
    if (!context) return
    context.save()
    context.globalCompositeOperation = 'source-over'
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.restore()
  }
  const updateHistoryButtons = () => {
    setCanUndo(historyIndex.current > 0)
    setCanRedo(historyIndex.current < history.current.length - 1)
  }
  const snapshot = (emit = true) => {
    const data = canvasRef.current?.toDataURL('image/png') ?? null
    if (!data) return
    history.current = history.current.slice(0, historyIndex.current + 1)
    history.current.push(data)
    historyIndex.current = history.current.length - 1
    updateHistoryButtons()
    if (emit) onChange(data)
  }
  const restore = (data: string) => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context) return
    const image = new Image()
    image.onload = () => { paintWhite(canvas); context.drawImage(image, 0, 0, canvas.width, canvas.height); onChange(data); updateHistoryButtons() }
    image.src = data
  }

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context) return
    paintWhite(canvas)
    if (value) {
      const image = new Image()
      image.onload = () => { context.drawImage(image, 0, 0, canvas.width, canvas.height); history.current = [canvas.toDataURL('image/png')]; historyIndex.current = 0; updateHistoryButtons() }
      image.src = value
    } else {
      history.current = [canvas.toDataURL('image/png')]
      historyIndex.current = 0
      updateHistoryButtons()
    }
    // The parent remounts this editor when a journal date changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const point = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    return { x: (event.clientX - rect.left) * (event.currentTarget.width / rect.width), y: (event.clientY - rect.top) * (event.currentTarget.height / rect.height) }
  }
  const start = (event: React.PointerEvent<HTMLCanvasElement>) => { event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); drawing.current = true; last.current = point(event) }
  const move = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current) return
    const context = event.currentTarget.getContext('2d')
    if (!context) return
    const next = point(event)
    context.save()
    context.lineWidth = size * (event.pressure > 0 ? Math.max(.65, event.pressure) : 1)
    context.lineCap = 'round'; context.lineJoin = 'round'
    context.globalCompositeOperation = tool === 'eraser' ? 'destination-out' : 'source-over'
    context.globalAlpha = tool === 'marker' ? .28 : 1
    context.strokeStyle = color
    context.beginPath(); context.moveTo(last.current.x, last.current.y); context.lineTo(next.x, next.y); context.stroke(); context.restore()
    last.current = next
  }
  const end = () => { if (!drawing.current) return; drawing.current = false; snapshot() }
  const undo = () => { if (!canUndo) return; historyIndex.current -= 1; restore(history.current[historyIndex.current]) }
  const redo = () => { if (!canRedo) return; historyIndex.current += 1; restore(history.current[historyIndex.current]) }
  const clear = () => { const canvas = canvasRef.current; if (!canvas) return; paintWhite(canvas); snapshot(false); onChange(null) }

  return <div className={`drawing-card${grid ? ' has-grid' : ''}`}>
    <div className="drawing-toolbar">
      <span><Pencil size={16} /> Bảng vẽ</span>
      <div className="drawing-tool-group" role="group" aria-label="Công cụ vẽ">
        <button type="button" className={tool === 'pen' ? 'is-active' : ''} onClick={() => setTool('pen')} title="Bút"><Pencil size={16} /></button>
        <button type="button" className={tool === 'marker' ? 'is-active' : ''} onClick={() => setTool('marker')} title="Bút đánh dấu"><Highlighter size={16} /></button>
        <button type="button" className={tool === 'eraser' ? 'is-active' : ''} onClick={() => setTool('eraser')} title="Tẩy"><Eraser size={16} /></button>
      </div>
      <div className="drawing-colors">{colors.map((item) => <button type="button" aria-label={`Màu ${item}`} className={color === item ? 'is-active' : ''} style={{ backgroundColor: item }} key={item} onClick={() => { setColor(item); setTool('pen') }} />)}</div>
      <label className="drawing-size">Nét<input aria-label="Độ dày nét" type="range" min="2" max="24" value={size} onChange={(event) => setSize(Number(event.target.value))} /></label>
      <button type="button" title="Hoàn tác" disabled={!canUndo} onClick={undo}><Undo2 size={16} /></button>
      <button type="button" title="Làm lại" disabled={!canRedo} onClick={redo}><Redo2 size={16} /></button>
      <button type="button" className={grid ? 'is-active' : ''} title="Lưới" onClick={() => setGrid((current) => !current)}><Grid3X3 size={16} /></button>
      <button type="button" title="Xóa toàn bộ" onClick={clear}><RotateCcw size={16} /></button>
    </div>
    <canvas ref={canvasRef} width={1600} height={900} className="drawing-canvas" onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} />
  </div>
}
