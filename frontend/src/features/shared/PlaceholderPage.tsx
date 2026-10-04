import { Construction } from 'lucide-react'

export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return <div className="page-content"><div className="card flex min-h-[420px] flex-col items-center justify-center px-8 text-center"><div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-blue-50 text-blue-600"><Construction size={25} /></div><h2 className="text-xl font-bold text-slate-800">{title}</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p><span className="mt-5 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">Đang phát triển</span></div></div>
}
