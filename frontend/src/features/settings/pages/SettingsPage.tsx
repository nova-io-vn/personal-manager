import { useEffect, useState, type ReactNode } from 'react'
import { Bot, LoaderCircle, LockKeyhole, Save, Send, Webhook } from 'lucide-react'
import { getApiError } from '../../../services/api'
import { settingsApi } from '../services/settingsApi'
import type { AppSettings } from '../types/settings'

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [telegramToken, setTelegramToken] = useState('')
  const [telegramTouched, setTelegramTouched] = useState(false)
  const [geminiKey, setGeminiKey] = useState('')
  const [geminiTouched, setGeminiTouched] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const load = async () => { try { setSettings(await settingsApi.get()) } catch (err) { setError(getApiError(err)) } finally { setLoading(false) } }
    void load()
  }, [])
  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => setSettings((current) => current ? { ...current, [key]: value } : current)
  const run = async (operation: () => Promise<string>) => { setBusy(true); setError(''); setNotice(''); try { setNotice(await operation()) } catch (err) { setError(getApiError(err)) } finally { setBusy(false) } }
  const save = () => run(async () => {
    if (!settings) return ''
    const payload: Partial<AppSettings> & { telegram_bot_token?: string | null; gemini_api_key?: string | null } = {
      telegram_enabled: settings.telegram_enabled,
      telegram_chat_id: settings.telegram_chat_id,
      gemini_enabled: settings.gemini_enabled,
      gemini_model: settings.gemini_model,
    }
    if (telegramTouched) payload.telegram_bot_token = telegramToken
    if (geminiTouched) payload.gemini_api_key = geminiKey
    setSettings(await settingsApi.update(payload))
    setTelegramToken(''); setTelegramTouched(false); setGeminiKey(''); setGeminiTouched(false)
    return 'Đã lưu cấu hình.'
  })

  if (loading) return <div className="page-content"><div className="card flex min-h-[420px] items-center justify-center gap-2 text-sm text-slate-400"><LoaderCircle className="animate-spin" size={17} /> Đang tải cài đặt…</div></div>
  if (!settings) return <div className="page-content"><div className="card p-8 text-center text-sm text-rose-600">{error || 'Không thể tải cài đặt.'}</div></div>

  const integrationReady = settings.telegram_token_configured && Boolean(settings.telegram_chat_id)
  return <div className="page-content settings-page">
    <div className="page-heading-row"><div><p className="eyebrow">Kết nối</p><h1>Cài đặt</h1><p className="page-subtitle">Chỉ quản lý hai dịch vụ ngoài: Gemini và Telegram.</p></div><button className="button-primary" onClick={() => void save()} disabled={busy}><Save size={16} /> {busy ? 'Đang lưu…' : 'Lưu cài đặt'}</button></div>
    {error && <Alert danger>{error}</Alert>}{notice && <Alert>{notice}</Alert>}
    <div className="settings-integrations">
      <Section icon={<Bot size={19} />} title="Gemini" description="Trợ lý đọc ngữ cảnh đã tổng hợp từ dữ liệu của bạn; không tự ý sửa dữ liệu.">
        <Toggle label="Bật Gemini" checked={settings.gemini_enabled} onChange={(value) => update('gemini_enabled', value)} />
        <div className="mt-5 space-y-4">
          <Field label="API Key"><input className="field" type="password" autoComplete="new-password" value={geminiKey} onChange={(event) => { setGeminiKey(event.target.value); setGeminiTouched(true) }} placeholder={settings.gemini_key_configured ? '•••••••• (đã lưu)' : 'Nhập Gemini API key'} /></Field>
          <Field label="Model"><input className="field" value={settings.gemini_model} onChange={(event) => update('gemini_model', event.target.value)} placeholder="gemini-3.5-flash" /></Field>
          <button className="button-secondary w-full" disabled={busy || !settings.gemini_key_configured} onClick={() => void run(async () => (await settingsApi.testGemini()).message)}><Bot size={15} /> Kiểm tra Gemini</button>
        </div>
      </Section>
      <Section icon={<Send size={19} />} title="Telegram" description="Nhận nhắc việc và tương tác với Personal Manager từ bot riêng của bạn.">
        <Toggle label="Bật Telegram" checked={settings.telegram_enabled} onChange={(value) => update('telegram_enabled', value)} />
        <div className="mt-5 space-y-4">
          <Field label="Bot Token"><input className="field" type="password" autoComplete="new-password" value={telegramToken} onChange={(event) => { setTelegramToken(event.target.value); setTelegramTouched(true) }} placeholder={settings.telegram_token_configured ? '•••••••• (đã lưu)' : 'Nhập bot token'} /></Field>
          <Field label="Chat ID"><input className="field" value={settings.telegram_chat_id ?? ''} onChange={(event) => update('telegram_chat_id', event.target.value)} placeholder="123456789" /></Field>
          <div className="grid gap-2 sm:grid-cols-2">
            <button className="button-secondary w-full" disabled={busy || !integrationReady} onClick={() => void run(async () => (await settingsApi.testTelegram()).message)}><Send size={15} /> Gửi thử</button>
            <button className="button-secondary w-full" disabled={busy || !integrationReady} onClick={() => void run(async () => (await settingsApi.registerTelegramWebhook()).message)}><Webhook size={15} /> Bật tương tác</button>
          </div>
        </div>
        <SecurityNote />
      </Section>
    </div>
  </div>
}

function Section({ icon, title, description, children }: { icon: ReactNode; title: string; description: string; children: ReactNode }) { return <section className="card settings-integration-card"><div className="settings-section-head"><div>{icon}</div><span><h2>{title}</h2><p>{description}</p></span></div>{children}</section> }
function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="block"><span className="field-label">{label}</span>{children}</label> }
function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) { return <label className="settings-toggle-row"><span>{label}</span><input className="setting-switch" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /></label> }
function Alert({ children, danger = false }: { children: ReactNode; danger?: boolean }) { return <div className={`notice ${danger ? 'notice-error' : 'notice-success'}`}>{children}</div> }
function SecurityNote() { return <div className="security-note"><LockKeyhole size={16} /><span>Khóa được lưu ở backend PostgreSQL và luôn bị che khi trả về ứng dụng.</span></div> }
