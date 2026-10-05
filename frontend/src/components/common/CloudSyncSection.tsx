import { Cloud, LogIn, LogOut, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { cloudSyncApi } from '../../services/cloudSyncApi'

export function CloudSyncSection() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loggedIn, setLoggedIn] = useState(Boolean(cloudSyncApi.token()))

  const run = async (action: 'login' | 'register') => {
    setBusy(true); setError(''); setMessage('')
    try {
      const result = action === 'login' ? await cloudSyncApi.login(email, password, 'desktop') : await cloudSyncApi.register(email, password)
      setLoggedIn(true); setMessage(`Đã đăng nhập ${result.user.email}. Có thể kết nối đồng bộ khi Sync API được triển khai.`)
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(detail || 'Không thể kết nối Cloud Sync.')
    } finally { setBusy(false) }
  }

  return <section className="card p-5"><div className="flex items-start gap-3 border-b border-slate-100 pb-4"><div className="grid h-9 w-9 place-items-center rounded-lg bg-blue-50 text-blue-600"><Cloud size={18} /></div><div><h3 className="font-bold text-slate-800">Đồng bộ dữ liệu</h3><p className="mt-1 text-xs text-slate-400">Đăng nhập để dùng tài khoản chung trên desktop và tablet.</p></div></div><div className="pt-5">{!cloudSyncApi.isConfigured && <p className="mb-4 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800">Chưa cấu hình VITE_CLOUD_SYNC_API_URL. Neon Database không tự cung cấp HTTP API; cần triển khai FastAPI Sync API trước.</p>}{loggedIn ? <div className="space-y-3"><p className="text-sm text-emerald-700">✓ Đã xác thực Cloud Sync trên thiết bị này.</p><button className="button-secondary" onClick={() => { cloudSyncApi.logout(); setLoggedIn(false); setMessage('Đã đăng xuất.') }}><LogOut size={15} /> Đăng xuất</button></div> : <div className="grid gap-3 md:grid-cols-2"><input className="field" type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} /><input className="field" type="password" placeholder="Mật khẩu (tối thiểu 8 ký tự)" value={password} onChange={(event) => setPassword(event.target.value)} /><div className="flex flex-wrap gap-2 md:col-span-2"><button className="button-primary" disabled={busy || !email || password.length < 8 || !cloudSyncApi.isConfigured} onClick={() => void run('login')}><LogIn size={15} /> Đăng nhập</button><button className="button-secondary" disabled={busy || !email || password.length < 8 || !cloudSyncApi.isConfigured} onClick={() => void run('register')}><RefreshCw size={15} /> Đăng ký</button></div></div>}{message && <p className="mt-3 text-sm text-emerald-700">{message}</p>}{error && <p className="mt-3 text-sm text-rose-600">{error}</p>}</div></section>
}
