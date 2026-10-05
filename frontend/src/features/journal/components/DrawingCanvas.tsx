import { useEffect, useRef, useState } from 'react'
import { Eraser, Pencil, RotateCcw } from 'lucide-react'

interface Props { value: string | null; onChange: (value: string | null) => void }

export function DrawingCanvas({ value, onChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null); const drawing = useRef(false); const last = useRef({ x: 0, y: 0 }); const [color, setColor] = useState('#173b63'); const [size, setSize] = useState(4)
  useEffect(() => { const canvas = canvasRef.current; if (!canvas) return; const context = canvas.getContext('2d'); if (!context) return; context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height); if (value) { const image = new Image(); image.onload = () => context.drawImage(image, 0, 0, canvas.width, canvas.height); image.src = value } }, [value])
  const point = (event: React.PointerEvent<HTMLCanvasElement>) => { const rect = event.currentTarget.getBoundingClientRect(); return { x: (event.clientX - rect.left) * (event.currentTarget.width / rect.width), y: (event.clientY - rect.top) * (event.currentTarget.height / rect.height) } }
  const start = (event: React.PointerEvent<HTMLCanvasElement>) => { event.currentTarget.setPointerCapture(event.pointerId); drawing.current = true; last.current = point(event) }
  const move = (event: React.PointerEvent<HTMLCanvasElement>) => { if (!drawing.current) return; const canvas = event.currentTarget; const context = canvas.getContext('2d'); if (!context) return; const next = point(event); context.strokeStyle = color; context.lineWidth = size; context.lineCap = 'round'; context.beginPath(); context.moveTo(last.current.x, last.current.y); context.lineTo(next.x, next.y); context.stroke(); last.current = next }
  const end = () => { if (!drawing.current) return; drawing.current = false; onChange(canvasRef.current?.toDataURL('image/png') ?? null) }
  const clear = () => { const canvas = canvasRef.current; const context = canvas?.getContext('2d'); if (!canvas || !context) return; context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height); onChange(null) }
  return <div className="drawing-card"><div className="drawing-toolbar"><span><Pencil size={15} /> Bảng vẽ</span><input aria-label="Màu bút" type="color" value={color} onChange={(event) => setColor(event.target.value)} /><select aria-label="Cỡ bút" value={size} onChange={(event) => setSize(Number(event.target.value))}><option value="2">Mảnh</option><option value="4">Vừa</option><option value="8">Đậm</option></select><button type="button" className="icon-button" title="Tẩy trắng" onClick={clear}><Eraser size={15} /></button><button type="button" className="icon-button" title="Xóa bản vẽ" onClick={clear}><RotateCcw size={15} /></button></div><canvas ref={canvasRef} width={1200} height={420} className="drawing-canvas" onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} /></div>
}
