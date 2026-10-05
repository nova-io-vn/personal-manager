import { lazy, Suspense } from 'react'
import { BrowserRouter, HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { BackendGate } from './components/common/BackendGate'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { isAndroid } from './services/api'

const CalendarPage = lazy(() => import('./features/calendar/pages/CalendarPage').then((module) => ({ default: module.CalendarPage })))
const DashboardPage = lazy(() => import('./features/dashboard/pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const FinancePage = lazy(() => import('./features/finance/pages/FinancePage').then((module) => ({ default: module.FinancePage })))
const HealthPage = lazy(() => import('./features/health/pages/HealthPage').then((module) => ({ default: module.HealthPage })))
const JournalPage = lazy(() => import('./features/journal/pages/JournalPage').then((module) => ({ default: module.JournalPage })))
const TasksPage = lazy(() => import('./features/tasks/pages/TasksPage').then((module) => ({ default: module.TasksPage })))
const AIPage = lazy(() => import('./features/ai/pages/AIPage').then((module) => ({ default: module.AIPage })))
const SettingsPage = lazy(() => import('./features/settings/pages/SettingsPage').then((module) => ({ default: module.SettingsPage })))
const BelongingsPage = lazy(() => import('./features/belongings/pages/BelongingsPage').then((module) => ({ default: module.BelongingsPage })))

function App() {
  const Router = window.personalManager || isAndroid ? HashRouter : BrowserRouter
  return <ErrorBoundary><BackendGate><Router><Suspense fallback={<div className="grid min-h-[60vh] place-items-center text-sm text-slate-400">Đang tải…</div>}><Routes><Route element={<AppShell />}><Route path="/" element={<DashboardPage />} /><Route path="/calendar" element={<CalendarPage />} /><Route path="/finance" element={<FinancePage />} /><Route path="/health" element={<HealthPage />} /><Route path="/journal" element={<JournalPage />} /><Route path="/tasks" element={<TasksPage />} /><Route path="/belongings" element={<BelongingsPage />} /><Route path="/ai" element={<AIPage />} /><Route path="/settings" element={<SettingsPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></Suspense></Router></BackendGate></ErrorBoundary>
}

export default App
