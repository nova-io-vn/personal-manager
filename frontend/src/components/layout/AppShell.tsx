import { useState } from 'react'
import { Activity, BookOpen, CalendarDays, CheckSquare, CircleDollarSign, HeartPulse, LayoutDashboard, Plus, Settings, Sparkles, WalletCards, X } from 'lucide-react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { NotificationBell } from '../../features/settings/components/NotificationBell'
import { DesktopUpdatePanel } from './DesktopUpdatePanel'

const navigation = [
  { label: 'Tổng quan', to: '/', icon: LayoutDashboard },
  { label: 'Lịch trình', to: '/calendar', icon: CalendarDays },
  { label: 'Tài chính', to: '/finance', icon: CircleDollarSign },
  { label: 'Sức khỏe', to: '/health', icon: HeartPulse },
  { label: 'Nhật ký', to: '/journal', icon: BookOpen },
  { label: 'Gemini', to: '/ai', icon: Sparkles },
  { label: 'Việc cần làm', to: '/tasks', icon: CheckSquare },
]

const quickActions = [
  { label: 'Giao dịch', detail: 'Thu, chi hoặc chuyển khoản', to: '/finance?quickAdd=transaction', icon: CircleDollarSign },
  { label: 'Lịch trình', detail: 'Thêm một sự kiện', to: '/calendar?quickAdd=schedule', icon: CalendarDays },
  { label: 'Cân nặng', detail: 'Ghi nhận số đo mới', to: '/health?quickAdd=measurement', icon: Activity },
  { label: 'Thực phẩm', detail: 'Mở sổ dinh dưỡng', to: '/health?quickAdd=food', icon: Plus },
  { label: 'Nhật ký', detail: 'Viết ghi chú hôm nay', to: '/journal?quickAdd=journal', icon: BookOpen },
  { label: 'Việc cần làm', detail: 'Ghi nhanh việc chưa có lịch', to: '/tasks', icon: CheckSquare },
]

export function AppShell() {
  const [quickOpen, setQuickOpen] = useState(false)
  const location = useLocation()
  const pageTitle = navigation.find((item) => item.to === location.pathname)?.label ?? 'Cài đặt'

  return <div className="app-shell">
    <header className="topbar">
      <Link to="/" className="brand" aria-label="Personal Manager — Tổng quan">
        <span className="brand-mark"><WalletCards size={20} strokeWidth={2.1} /></span>
        <span className="brand-copy"><strong>Personal Manager</strong><small>Không gian của bạn</small></span>
      </Link>
      <nav className="top-nav" aria-label="Điều hướng chính">
        {navigation.map(({ label, to, icon: Icon }) => <NavLink end={to === '/'} key={to} to={to} className={({ isActive }) => `top-nav-link${isActive ? ' is-active' : ''}`}>
          <Icon size={17} strokeWidth={1.9} /><span>{label}</span>
        </NavLink>)}
      </nav>
      <div className="topbar-actions">
        <div className="quick-add-wrap">
          <button className={`icon-button quick-add-button${quickOpen ? ' is-open' : ''}`} aria-label="Thêm nhanh" aria-expanded={quickOpen} onClick={() => setQuickOpen((value) => !value)}>
            {quickOpen ? <X size={18} /> : <Plus size={19} />}<span className="quick-add-label">Thêm</span>
          </button>
          {quickOpen && <><button className="menu-dismiss" aria-label="Đóng menu thêm nhanh" onClick={() => setQuickOpen(false)} /><div className="quick-menu" role="menu"><p className="quick-menu-heading">Tạo mới</p>{quickActions.map(({ label, detail, to, icon: Icon }) => <Link role="menuitem" key={label} to={to} className="quick-menu-item" onClick={() => setQuickOpen(false)}><span className="quick-menu-icon"><Icon size={17} /></span><span><strong>{label}</strong><small>{detail}</small></span></Link>)}</div></>}
        </div>
        <NotificationBell />
        <Link className={`icon-button settings-button${location.pathname === '/settings' ? ' is-open' : ''}`} to="/settings" aria-label="Cài đặt" title="Cài đặt"><Settings size={18} /></Link>
      </div>
    </header>
    <div className="mobile-page-label">{pageTitle}</div>
    <main className="app-main"><Outlet />{location.pathname === '/settings' && <div className="page-content"><DesktopUpdatePanel /></div>}</main>
  </div>
}
