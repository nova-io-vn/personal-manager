import { DrawingCanvas } from './DrawingCanvas'

export function DrawingCanvasWithJournalHeading(props: { value: string | null; onChange: (value: string | null) => void }) {
  return <><h2 className="sr-only">Nhật ký</h2><DrawingCanvas {...props} /></>
}
