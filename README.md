# Personal Manager 0.1.0

Personal management app for Windows and Android tablets. Both clients use the shared FastAPI API and PostgreSQL database so changes are visible on both devices. Gemini and Telegram are optional integrations.

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

Both require internet and user-provided credentials. Configure them in Settings. Gemini receives request-relevant structured summaries and cannot write application data. Telegram can send notifications; after `PUBLIC_BASE_URL` is configured on the backend, use **Bật tương tác** to register the webhook. Send `/tasks` to receive completion buttons, or a message such as `Đã ăn mất 50 nghìn` and confirm before Finance records it. Keys are masked in API/UI responses and are not logged, but remain stored in PostgreSQL without application-level encryption.

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

The generated APK is `frontend\android\app\build\outputs\apk\debug\app-debug.apk`. It uses the same shared API/PostgreSQL data as Desktop and therefore requires an internet connection.

## CI and release pipeline

`.github/workflows/ci.yml` validates pushes/PRs. `.github/workflows/release.yml` runs only for version tags such as `v0.2.0`, builds the Windows installer and signed Android APK, then publishes them to GitHub Releases. A normal push does not update installed apps; create a version tag after CI passes.

Configure these GitHub Actions secrets for a stable Android signing identity: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD`. Never replace the signing keystore after publishing an APK if users need in-place updates. A sync server/domain has not yet been supplied; no cloud data is being sent anywhere.

Tagging is a release action (not a normal update):

```powershell
git push origin main
git tag v0.2.0
git push origin v0.2.0
```
