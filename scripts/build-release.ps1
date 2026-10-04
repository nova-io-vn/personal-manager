$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Invoke-Checked([string]$Name, [scriptblock]$Action) {
    Write-Host "`n== $Name ==" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
}

Push-Location (Join-Path $repo 'backend')
try {
    $python = Join-Path $repo 'backend\.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) { throw 'Create backend\.venv and install backend\requirements.txt first.' }
    Invoke-Checked 'Backend tests' { & $python -m pytest }
    Invoke-Checked 'Backend executable' { & $python -m PyInstaller --clean --noconfirm personal-manager-backend.spec }
} finally { Pop-Location }

Push-Location (Join-Path $repo 'frontend')
try {
    Invoke-Checked 'Frontend lint' { npm.cmd run lint }
    Invoke-Checked 'Frontend production build' { npm.cmd run build }
    Invoke-Checked 'Playwright E2E' { npm.cmd run test:e2e }
} finally { Pop-Location }

Push-Location (Join-Path $repo 'desktop')
try {
    Invoke-Checked 'Windows installer' { npm.cmd run dist }
} finally { Pop-Location }

Write-Host "`nRelease artifact: $repo\desktop\release\Personal-Manager-Setup-0.1.0.exe" -ForegroundColor Green
