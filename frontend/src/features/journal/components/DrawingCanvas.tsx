import { useEffect, useRef, useState } from 'react'
import { Circle, Download, Eraser, Expand, Highlighter, Minus, Pencil, Redo2, RotateCcw, Square, Undo2 } from 'lucide-react'

interface Props { value: string | null; onChange: (value: string | null) => void }
type Tool = 'pen' | 'marker' | 'eraser' | 'line' | 'rectangle' | 'circle'
type Paper = 'grid' | 'dots' | 'plain'
const colors = ['#173b63', '#2563eb', '#dc2626', '#f59e0b', '#16a34a', '#7c3aed', '#111827']

export function DrawingCanvas({ value, onChange }: Props) {
  const cardRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const drawing = useRef(false)
  const last = useRef({ x: 0, y: 0 })
  const shapeStart = useRef<ImageData | null>(null)
  const history = useRef<string[]>([])
  const historyIndex = useRef(-1)
  const [tool, setTool] = useState<Tool>('pen')
  const [color, setColor] = useState('#173b63')
  const [size, setSize] = useState(4)
  const [paper, setPaper] = useState<Paper>('grid')
  const [canUndo, setCanUndo] = useState(false)
  const [canRedo, setCanRedo] = useState(false)

  const paintWhite = (canvas: HTMLCanvasElement) => {
    const context = canvas.getContext('2d')
    if (!context) return
    context.save(); context.globalCompositeOperation = 'source-over'; context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height); context.restore()
  }
  const updateHistoryButtons = () => { setCanUndo(historyIndex.current > 0); setCanRedo(historyIndex.current < history.current.length - 1) }
  const snapshot = (emit = true) => {
    const data = canvasRef.current?.toDataURL('image/png') ?? null
    if (!data) return
    history.current = history.current.slice(0, historyIndex.current + 1)
    history.current.push(data); historyIndex.current = history.current.length - 1; updateHistoryButtons()
    if (emit) onChange(data)
  }
  const restore = (data: string) => {
    const canvas = canvasRef.current; const context = canvas?.getContext('2d')
    if (!canvas || !context) return
    const image = new Image()
    image.onload = () => { paintWhite(canvas); context.drawImage(image, 0, 0, canvas.width, canvas.height); onChange(data); updateHistoryButtons() }
    image.src = data
  }

  useEffect(() => {
    const canvas = canvasRef.current; const context = canvas?.getContext('2d')
    if (!canvas || !context) return
    paintWhite(canvas)
    if (value) {
      const image = new Image()
      image.onload = () => { context.drawImage(image, 0, 0, canvas.width, canvas.height); history.current = [canvas.toDataURL('image/png')]; historyIndex.current = 0; updateHistoryButtons() }
      image.src = value
    } else {
      history.current = [canvas.toDataURL('image/png')]; historyIndex.current = 0; updateHistoryButtons()
    }
    // The journal editor is remounted when a date changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const point = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    return { x: (event.clientX - rect.left) * (event.currentTarget.width / rect.width), y: (event.clientY - rect.top) * (event.currentTarget.height / rect.height) }
  }
  const configureStroke = (context: CanvasRenderingContext2D, pressure = 1) => {
    context.lineWidth = size * Math.max(.65, pressure)
    context.lineCap = 'round'; context.lineJoin = 'round'; context.strokeStyle = color
    context.globalCompositeOperation = tool === 'eraser' ? 'destination-out' : 'source-over'
    context.globalAlpha = tool === 'marker' ? .28 : 1
  }
  const start = (event: React.PointerEvent<HTMLCanvasElement>) => {
    event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); drawing.current = true; last.current = point(event)
    shapeStart.current = event.currentTarget.getContext('2d')?.getImageData(0, 0, event.currentTarget.width, event.currentTarget.height) ?? null
  }
  const move = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current) return
    const context = event.currentTarget.getContext('2d'); if (!context) return
    const next = point(event); const isShape = ['line', 'rectangle', 'circle'].includes(tool)
    if (isShape && shapeStart.current) context.putImageData(shapeStart.current, 0, 0)
    context.save(); configureStroke(context, event.pressure || 1); context.beginPath()
    if (tool === 'line') { context.moveTo(last.current.x, last.current.y); context.lineTo(next.x, next.y) }
    else if (tool === 'rectangle') context.rect(last.current.x, last.current.y, next.x - last.current.x, next.y - last.current.y)
    else if (tool === 'circle') {
      const radius = Math.hypot(next.x - last.current.x, next.y - last.current.y)
      context.arc(last.current.x, last.current.y, radius, 0, Math.PI * 2)
    } else { context.moveTo(last.current.x, last.current.y); context.lineTo(next.x, next.y); last.current = next }
    context.stroke(); context.restore()
  }
  const end = () => { if (!drawing.current) return; drawing.current = false; shapeStart.current = null; snapshot() }
  const undo = () => { if (!canUndo) return; historyIndex.current -= 1; restore(history.current[historyIndex.current]) }
  const redo = () => { if (!canRedo) return; historyIndex.current += 1; restore(history.current[historyIndex.current]) }
  const clear = () => { const canvas = canvasRef.current; if (!canvas) return; paintWhite(canvas); snapshot(false); onChange(null) }
  const download = () => {
    const data = canvasRef.current?.toDataURL('image/png'); if (!data) return
    const link = document.createElement('a'); link.href = data; link.download = `nhat-ky-${new Date().toISOString().slice(0, 10)}.png`; link.click()
  }
  const fullscreen = () => { if (cardRef.current?.requestFullscreen) void cardRef.current.requestFullscreen() }
  const toolButton = (name: Tool, label: string, icon: React.ReactNode) => <button type="button" className={tool === name ? 'is-active' : ''} onClick={() => setTool(name)} title={label} aria-label={label}>{icon}</button>

  return <div ref={cardRef} className={`drawing-card paper-${paper}`}>
    <div className="drawing-toolbar">
      <span><Pencil size={17} /> Sổ vẽ</span>
      <div className="drawing-tool-group" role="group" aria-label="Công cụ vẽ">
        {toolButton('pen', 'Bút', <Pencil size={16} />)}
        {toolButton('marker', 'Bút đánh dấu', <Highlighter size={16} />)}
        {toolButton('eraser', 'Tẩy', <Eraser size={16} />)}
        {toolButton('line', 'Đường thẳng', <Minus size={16} />)}
        {toolButton('rectangle', 'Hình chữ nhật', <Square size={16} />)}
        {toolButton('circle', 'Hình tròn', <Circle size={16} />)}
      </div>
      <div className="drawing-colors">{colors.map((item) => <button type="button" aria-label={`Màu ${item}`} className={color === item ? 'is-active' : ''} style={{ backgroundColor: item }} key={item} onClick={() => { setColor(item); if (tool === 'eraser') setTool('pen') }} />)}<input aria-label="Màu tùy chọn" type="color" value={color} onChange={(event) => setColor(event.target.value)} /></div>
      <label className="drawing-size">Nét <input aria-label="Độ dày nét" type="range" min="2" max="28" value={size} onChange={(event) => setSize(Number(event.target.value))} /><b>{size}</b></label>
      <select aria-label="Kiểu giấy" value={paper} onChange={(event) => setPaper(event.target.value as Paper)}><option value="grid">Ô vuông</option><option value="dots">Chấm</option><option value="plain">Trắng</option></select>
      <div className="drawing-tool-group drawing-actions">
        <button type="button" title="Hoàn tác" aria-label="Hoàn tác" disabled={!canUndo} onClick={undo}><Undo2 size={16} /></button>
        <button type="button" title="Làm lại" aria-label="Làm lại" disabled={!canRedo} onClick={redo}><Redo2 size={16} /></button>
        <button type="button" title="Toàn màn hình" aria-label="Toàn màn hình" onClick={fullscreen}><Expand size={16} /></button>
        <button type="button" title="Tải ảnh" aria-label="Tải ảnh" onClick={download}><Download size={16} /></button>
        <button type="button" title="Xóa toàn bộ" aria-label="Xóa toàn bộ" onClick={clear}><RotateCcw size={16} /></button>
      </div>
    </div>
    <canvas ref={canvasRef} width={1800} height={1100} className="drawing-canvas" onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} />
  </div>
}
