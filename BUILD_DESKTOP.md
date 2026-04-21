# Desktop Build

This project now supports a two-stage desktop build:

1. Build the Django backend into a standalone folder with PyInstaller.
2. Bundle Electron and the backend together with `electron-builder`.

## Prerequisites

- Windows with PowerShell
- Python dependencies installed:
  - `pip install -r requirements.txt`
  - `pip install pyinstaller`
- Node dependencies installed:
  - `npm install`

## 1. Build the backend

```powershell
npm run build:backend
```

This creates:

- `dist/brandregistry-backend/`
- `electron/resources/backend/brandregistry-backend/`

## 2. Package the desktop app

For a portable unpacked build:

```powershell
npm run pack:win
```

For a Windows installer:

```powershell
npm run dist:win
```

The final desktop artifacts are written to:

- `release/`

## Development mode

```powershell
npm start
```

In development, Electron starts `python run_app.py`.
In packaged mode, Electron starts `backend.exe` from `resources/backend`.
