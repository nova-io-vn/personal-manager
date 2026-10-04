import { useState } from 'react'
import { X } from 'lucide-react'
import type { Account, AccountType } from '../types/finance'
import { accountLabels } from '../types/finance'

export function AccountForm({ editing, onClose, onSubmit, busy }: { editing: Account | null; onClose: () => void; onSubmit: (payload: { name: string; type: AccountType; initial_balance: string }, id?: number) => Promise<void>; busy: boolean }) {
  const [name, setName] = useState(editing?.name ?? '')
  const [type, setType] = useState<AccountType>(editing?.type ?? 'BANK')
  const [balance, setBalance] = useState(editing?.initial_balance ?? '')
  const submit = async (event: React.FormEvent) => { event.preventDefault(); await onSubmit({ name, type, initial_balance: balance }, editing?.id) }
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}><div className="flex items-center justify-between border-b border-slate-100 px-6 py-4"><h2 className="font-bold text-slate-800">{editing ? 'Sửa tài khoản' : 'Thêm tài khoản'}</h2><button type="button" onClick={onClose} className="text-slate-400" aria-label="Đóng"><X size={19} /></button></div><div className="grid gap-4 px-6 py-5"><div><label className="field-label" htmlFor="account-name">Tên tài khoản</label><input id="account-name" className="field" required value={name} onChange={(event) => setName(event.target.value)} placeholder="Ví dụ: Tài khoản chính" /></div><div><label className="field-label" htmlFor="account-type">Loại tài khoản</label><select id="account-type" className="field" value={type} onChange={(event) => setType(event.target.value as AccountType)}>{Object.entries(accountLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>{!editing && <div><label className="field-label" htmlFor="account-balance">Số dư ban đầu</label><input id="account-balance" className="field" type="number" step="0.01" value={balance} onChange={(event) => setBalance(event.target.value)} /></div>}</div><div className="flex justify-end gap-2 border-t border-slate-100 px-6 py-4"><button type="button" className="button-secondary" onClick={onClose}>Hủy</button><button type="submit" className="button-primary" disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu tài khoản'}</button></div></form></div>
}
