# Personal Manager 0.1.0

Local-first personal management app for Windows. The desktop installer bundles the React UI, a loopback-only FastAPI service, and SQLite. Personal data is kept on the computer; Gemini and Telegram are optional online integrations.

## Development

Backend (Python 3.12):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend, in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The API is http://127.0.0.1:8000 and Swagger is http://127.0.0.1:8000/docs. In Git Bash, activate Python with `source .venv/Scripts/activate`.

## Tests and release build

```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest
cd ..\frontend; npm.cmd run lint; npm.cmd run build; npm.cmd run test:e2e
cd ..; .\scripts\build-release.ps1
```

The release script builds/tests the backend, builds the web UI, runs isolated Playwright flows, packages the backend, then creates the per-user Windows installer using electron-builder. It requires the declared Python and Node dependencies and Windows build tools; no Docker is used.

## Install and local data

Run `desktop\release\Personal-Manager-Setup-0.1.0.exe` and install for the current user. The desktop shell starts the bundled backend on a dynamically selected loopback port and serves the bundled UI. No Python, Node, terminal, or internet connection is needed for normal use.

Windows application data lives under `%APPDATA%\Personal Manager\` (Electron `userData`), including `personal.db`, `backups\`, and rotating backend logs. It is outside the installation directory and is preserved when uninstalling. Do not manually edit the database while the app is running.

The schema is managed by Alembic. Fresh databases migrate from zero. A pre-Alembic database is checked for every current table and column before the initial revision is stamped; if it is incomplete, startup stops without dropping tables or deleting data. Back up important data before installing an update that changes the schema.

## Backup and restore

Use Settings → Data. A backup is a ZIP containing an SQLite Online Backup snapshot and a manifest; it is integrity-checked before restore. Restore creates an automatic pre-restore safety backup, replaces the database, and requires restarting the application to reload data. In Electron, native file dialogs select the archive/destination. Backups contain the local database, including configured Telegram/Gemini credentials; SQLite and backup files are not encrypted, so store backups securely.

## Gemini and Telegram

Both are optional and require internet plus user-provided credentials. Configure them in Settings. Gemini receives only request-relevant structured summaries, and journal text is included only when relevant to the question; the model cannot write to application data. Telegram sends notification messages. Keys are masked in API/UI responses and are not logged, but they are stored in local SQLite without encryption. Never share the database or backup casually.

## Troubleshooting

- Backend startup error: check `%APPDATA%\Personal Manager\logs\backend.log`; close any second app instance and retry. The app binds only to `127.0.0.1` and picks a free port.
- Database/migration error: do not delete `personal.db`; make a copy and contact support with the safe error message/log (remove personal details first).
- Invalid restore: use a Personal Manager ZIP from a compatible schema version. The current restore endpoint rejects incompatible or corrupt archives before touching the active database.
- Gemini/Telegram unavailable: local modules continue to work offline; check network and integration settings. Test actions return safe status messages and do not expose credentials.

## Build parts separately

```powershell
cd backend; .\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm personal-manager-backend.spec
cd ..\frontend; npm.cmd run lint; npm.cmd run build
cd ..\desktop; npm.cmd run dist
```

## Android tablet (offline preview)

The React UI is wrapped with Capacitor 8. On Android, its existing Finance, Calendar, Health/Nutrition and Journal service calls are handled by a device-local SQLite adapter; the tablet does not need the Windows FastAPI process. Build a debug APK with:

```powershell
cd frontend
npm ci
npm run build
npx cap sync android
cd android
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
.\gradlew.bat assembleDebug
```

The generated APK is `frontend\android\app\build\outputs\apk\debug\app-debug.apk`. Tablet data is stored in the Android app's private SQLite database and is separate from Windows data. Uninstalling the app may remove that data. There is no cloud sync yet. Gemini, Telegram, background notification scheduling, and backup/restore are unavailable in this offline Android build; do not enter integration credentials there.

## CI and release pipeline

`.github/workflows/ci.yml` runs backend tests, frontend lint/build, and Playwright on pushes/PRs to `main`/`develop`. `.github/workflows/release.yml` runs only for version tags such as `v0.2.0`; Android offline storage now exists, but cloud sync/device authorization do not. GitHub Release publication remains gated by the repository variable `MOBILE_RELEASE_READY=true` until Android backup and release-signing are configured and the full mobile flows are validated.

Configure these GitHub Actions secrets for a stable Android signing identity: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD`. Never replace the signing keystore after publishing an APK if users need in-place updates. A sync server/domain has not yet been supplied; no cloud data is being sent anywhere.

Tagging is a release action (not a normal update):

```powershell
git push origin main
git tag v0.2.0
git push origin v0.2.0
```
