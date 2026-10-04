import { useEffect, useState, type ReactNode } from 'react'
import { LoaderCircle, RefreshCw } from 'lucide-react'
import { api } from '../../services/api'

export function BackendGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<'loading' | 'ready' | 'failed'>('loading')
  const check = async () => { try { await api.get('/health', { timeout: 5000 }); setState('ready') } catch { setState('failed') } }
  const retry = () => { setState('loading'); void check() }
  useEffect(() => { let active = true; api.get('/health', { timeout: 5000 }).then(() => { if (active) setState('ready') }).catch(() => { if (active) setState('failed') }); return () => { active = false } }, [])
  if (state === 'loading') return <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500"><div className="flex items-center gap-2"><LoaderCircle className="animate-spin" size={18} /> Đang khởi động Personal Manager…</div></div>
  if (state === 'failed') return <div className="grid min-h-screen place-items-center bg-slate-50 p-6"><div className="card max-w-md p-8 text-center"><h1 className="text-xl font-bold text-slate-800">Không thể kết nối dịch vụ Personal Manager.</h1><p className="mt-2 text-sm text-slate-500">Dịch vụ dữ liệu cục bộ chưa sẵn sàng. Hãy thử lại.</p><button className="button-primary mt-5" onClick={retry}><RefreshCw size={16} /> Thử lại</button></div></div>
  return children
}
