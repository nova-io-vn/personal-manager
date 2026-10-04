import { Pencil, Trash2 } from 'lucide-react'
import type { Account } from '../types/finance'
import { accountLabels } from '../types/finance'
import { formatVnd } from '../../../utils/format'

export function AccountList({ accounts, onEdit, onDelete }: { accounts: Account[]; onEdit: (account: Account) => void; onDelete: (account: Account) => void }) {
  return <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h3 className="font-bold text-slate-800">Tài khoản</h3><p className="mt-0.5 text-xs text-slate-400">Số dư hiện tại</p></div></div>{accounts.length === 0 ? <p className="p-5 text-sm text-slate-400">Chưa có tài khoản.</p> : <div className="divide-y divide-slate-100">{accounts.map((account) => <div className="flex items-center justify-between gap-3 px-5 py-3.5" key={account.id}><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-700">{account.name}</p><p className="mt-0.5 text-xs text-slate-400">{accountLabels[account.type]}</p></div><div className="flex items-center gap-2"><p className="text-sm font-bold text-slate-700">{formatVnd(Number(account.current_balance))}</p><button className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-blue-600" onClick={() => onEdit(account)} aria-label={`Sửa ${account.name}`}><Pencil size={14} /></button><button className="rounded p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600" onClick={() => onDelete(account)} aria-label={`Xóa ${account.name}`}><Trash2 size={14} /></button></div></div>)}</div>}</div>
}
