import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { failed: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }
  static getDerivedStateFromError(): State { return { failed: true } }
  componentDidCatch() { /* Stack details intentionally remain outside the user-facing UI. */ }
  render() { if (this.state.failed) return <div className="grid min-h-screen place-items-center bg-slate-50 p-6"><div className="card max-w-md p-8 text-center"><h1 className="text-xl font-bold text-slate-800">Đã xảy ra lỗi.</h1><p className="mt-2 text-sm text-slate-500">Ứng dụng không thể hiển thị trang này an toàn.</p><button className="button-primary mt-5" onClick={() => window.location.reload()}>Tải lại ứng dụng</button></div></div>; return this.props.children }
}
