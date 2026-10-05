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
} finally { Pop-Location }

Push-Location (Join-Path $repo 'frontend')
try {
    $frontendPackage = Get-Content (Join-Path $repo 'frontend\package.json') -Raw | ConvertFrom-Json
    $env:VITE_APP_VERSION = $frontendPackage.version
    Invoke-Checked 'Frontend lint' { npm.cmd run lint }
    Invoke-Checked 'Frontend production build' { npm.cmd run build }
    Invoke-Checked 'Playwright E2E' { npm.cmd run test:e2e }
} finally { Pop-Location }

Push-Location (Join-Path $repo 'desktop')
try {
    Invoke-Checked 'Windows installer' { npm.cmd run dist }
} finally { Pop-Location }

$desktopPackage = Get-Content (Join-Path $repo 'desktop\package.json') -Raw | ConvertFrom-Json
Write-Host "`nRelease artifact: $repo\desktop\release\Personal-Manager-Setup-$($desktopPackage.version).exe" -ForegroundColor Green
