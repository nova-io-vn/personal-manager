import { useEffect, useState } from 'react'
import { Download, RefreshCw, RotateCw } from 'lucide-react'

export function DesktopUpdatePanel() {
  const desktop = window.personalManager
  const [version, setVersion] = useState(import.meta.env.VITE_APP_VERSION || '0.1.0')
  const [available, setAvailable] = useState<string | null>(null)
  const [downloaded, setDownloaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!desktop) return
    let active = true
    const stopAvailable = desktop.onUpdateAvailable(({ version: next }) => { if (active) setAvailable(next) })
    const stopDownloaded = desktop.onUpdateDownloaded(() => { if (active) setDownloaded(true) })
    void desktop.getVersion().then((current) => { if (active) setVersion(current) })
    return () => { active = false; stopAvailable(); stopDownloaded() }
  }, [desktop])

  const check = async () => {
    if (!desktop) {
      setMessage('Kiểm tra cập nhật khả dụng trong ứng dụng Windows.')
      return
    }
    setBusy(true)
    setMessage('')
    try {
      const result = await desktop.checkForUpdates()
      if (result.error) setMessage(result.error)
      else if (result.available) setAvailable(result.version ?? null)
      else setMessage(result.supported ? 'Bạn đang sử dụng phiên bản mới nhất.' : 'Chỉ kiểm tra cập nhật trong bản cài đặt Windows.')
    } catch {
      setMessage('Không thể kiểm tra cập nhật. Hãy thử lại sau.')
    } finally {
      setBusy(false)
    }
  }

  const download = async () => {
    if (!desktop) return
    setBusy(true)
    const result = await desktop.downloadUpdate()
    if (!result.success) setMessage(result.message ?? 'Không thể tải bản cập nhật.')
    else setMessage('Đang tải bản cập nhật…')
    setBusy(false)
  }

  return (
    <section className="card mt-5 p-5" aria-labelledby="app-update-heading">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 id="app-update-heading" className="font-bold text-slate-800">Ứng dụng</h3>
          <p className="mt-1 text-sm text-slate-500">Phiên bản {version}{available ? ` · Có phiên bản ${available}` : ''}</p>
          {message && <p role="status" className="mt-2 text-sm text-slate-600">{message}</p>}
        </div>
        {downloaded
          ? <button type="button" className="button-primary" onClick={() => void desktop?.installUpdate()}><RotateCw size={15} /> Khởi động lại để cập nhật</button>
          : available
            ? <button type="button" className="button-primary" disabled={busy} onClick={() => void download()}><Download size={15} /> Tải bản cập nhật</button>
            : <button type="button" className="button-secondary" disabled={busy} onClick={() => void check()}><RefreshCw size={15} className={busy ? 'animate-spin' : ''} /> Kiểm tra cập nhật</button>}
      </div>
    </section>
  )
}
