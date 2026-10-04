import { spawn, execFileSync } from 'node:child_process'
import { createRequire } from 'node:module'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendDir = path.resolve(scriptDir, '..')
const repository = path.resolve(frontendDir, '..')
const backendDir = path.join(repository, 'backend')
const testData = path.join(frontendDir, `.playwright-userdata-${Date.now()}`)
const env = { ...process.env, PERSONAL_MANAGER_DATA_DIR: testData, CORS_ORIGINS: 'http://127.0.0.1:5173' }
const children = []

function start(command, args, options) {
  const child = spawn(command, args, { stdio: 'inherit', ...options })
  children.push(child)
  return child
}

async function waitFor(url, child) {
  const deadline = Date.now() + 45000
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Test server exited early (${child.exitCode}): ${url}`)
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch { /* Retry during local server startup. */ }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`Timed out waiting for ${url}`)
}

function stopTestServers() {
  if (process.platform === 'win32') {
    for (const child of [...children].reverse()) {
      if (!child.pid) continue
      try { execFileSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore', timeout: 10000 }) } catch { /* The process tree may already have exited. */ }
    }
  } else {
    for (const child of children) if (child.pid && child.exitCode === null) child.kill('SIGTERM')
  }
}

let testExitCode = 1
try {
  const python = path.join(backendDir, '.venv', 'Scripts', 'python.exe')
  const backend = start(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '18766'], {
    cwd: backendDir,
    env,
  })
  const viteCli = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js')
  const frontend = start(process.execPath, [viteCli, '--host', '127.0.0.1', '--port', '5173'], {
    cwd: frontendDir,
    env: { ...env, VITE_API_BASE_URL: 'http://127.0.0.1:18766/api' },
  })
  await Promise.all([waitFor('http://127.0.0.1:18766/api/health', backend), waitFor('http://127.0.0.1:5173', frontend)])
  const require = createRequire(import.meta.url)
  const { program } = require('playwright/lib/program')
  await program.parseAsync(['node', 'playwright', 'test', '--config', 'playwright.config.ts'])
  testExitCode = process.exitCode ?? 0
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.stack : String(error)}\n`)
} finally {
  stopTestServers()
}
process.exitCode = testExitCode
