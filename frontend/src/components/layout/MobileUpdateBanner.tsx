import { Download, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Capacitor } from '@capacitor/core'
import { checkMobileUpdate, type MobileUpdateInfo } from '../../services/mobileUpdate'

export function MobileUpdateBanner() {
  const [update, setUpdate] = useState<MobileUpdateInfo | null>(null); const [dismissed, setDismissed] = useState(false)
  useEffect(() => {
    if (Capacitor.getPlatform() !== 'android') return
    const lastCheck = Number(localStorage.getItem('pm_update_checked_at') ?? 0)
    if (Date.now() - lastCheck < 12 * 60 * 60 * 1000) return
    localStorage.setItem('pm_update_checked_at', String(Date.now()))
    void checkMobileUpdate().then(setUpdate).catch(() => undefined)
  }, [])
  if (!update || dismissed) return null
  return <div className="mobile-update-banner" role="status"><div><strong>Có phiên bản mới {update.latestVersion}</strong><span>Hãy tải APK từ GitHub Release chính thức để cập nhật.</span></div><a className="button-primary" href={update.apkUrl} target="_blank" rel="noreferrer"><Download size={15} /> Tải APK</a><button className="icon-button" aria-label="Để sau" onClick={() => setDismissed(true)}><X size={16} /></button></div>
}
