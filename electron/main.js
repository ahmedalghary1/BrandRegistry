const { app, BrowserWindow, Menu, dialog, ipcMain } = require("electron");
const { execFile, spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const path = require("path");

const APP_TITLE = "نظام إدارة العلامات والنماذج الصناعية";
const PROJECT_ROOT = path.resolve(__dirname, "..");
const RUN_APP_PY = path.join(PROJECT_ROOT, "run_app.py");
const SPLASH_HTML = path.join(__dirname, "splash.html");
const ICON_PATH = path.join(PROJECT_ROOT, "static", "dashboard_files", "logo-gold.png");
const BACKEND_DIST_NAME = "brandregistry-backend";
const BACKEND_EXE_NAME = process.platform === "win32" ? `${BACKEND_DIST_NAME}.exe` : BACKEND_DIST_NAME;
const BACKUP_PREFERENCES_FILE = "backup-preferences.json";

let djangoProcess = null;
let mainWindow = null;
let splashWindow = null;
let appPort = null;
let isQuitting = false;
let bootstrapErrorShown = false;
let isHandlingClosePrompt = false;

function getBackupPreferencesPath() {
  return path.join(app.getPath("userData"), BACKUP_PREFERENCES_FILE);
}

function loadBackupPreferences() {
  try {
    const filePath = getBackupPreferencesPath();
    if (!fs.existsSync(filePath)) {
      return {};
    }

    const content = fs.readFileSync(filePath, "utf8");
    return JSON.parse(content);
  } catch (error) {
    return {};
  }
}

function saveBackupPreferences(preferences) {
  const filePath = getBackupPreferencesPath();
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(preferences, null, 2), "utf8");
}

function getPreferredBackupDirectory() {
  const preferences = loadBackupPreferences();
  const directory = preferences.preferredBackupDirectory;

  if (!directory || !fs.existsSync(directory)) {
    return null;
  }

  return directory;
}

function setPreferredBackupDirectory(directory) {
  saveBackupPreferences({ preferredBackupDirectory: directory });
}

function clearPreferredBackupDirectory() {
  saveBackupPreferences({});
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 620,
    height: 420,
    title: `${APP_TITLE} - جاري الإقلاع`,
    resizable: false,
    minimizable: false,
    maximizable: false,
    show: true,
    center: true,
    autoHideMenuBar: true,
    backgroundColor: "#0f4c5c",
    icon: fs.existsSync(ICON_PATH) ? ICON_PATH : undefined,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  splashWindow.loadFile(SPLASH_HTML);
}

function createMainWindow(targetUrl) {
  mainWindow = new BrowserWindow({
    title: APP_TITLE,
    width: 1480,
    height: 960,
    minWidth: 1160,
    minHeight: 760,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: "#f4f7fb",
    icon: fs.existsSync(ICON_PATH) ? ICON_PATH : undefined,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: false,
      nodeIntegration: false,
      devTools: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (appPort && !url.startsWith(`http://127.0.0.1:${appPort}`)) {
      event.preventDefault();
    }
  });

  mainWindow.once("ready-to-show", () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
  });

  mainWindow.on("close", async (event) => {
    if (isQuitting || isHandlingClosePrompt) {
      return;
    }

    event.preventDefault();
    isHandlingClosePrompt = true;

    try {
      const choice = await dialog.showMessageBox(mainWindow, {
        type: "question",
        buttons: [
          "إنشاء نسخة احتياطية ثم إغلاق",
          "إغلاق بدون نسخة احتياطية",
          "إلغاء",
        ],
        defaultId: 0,
        cancelId: 2,
        noLink: true,
        title: APP_TITLE,
        message: "هل تريد إنشاء نسخة احتياطية من قاعدة البيانات قبل إغلاق التطبيق؟",
        detail: "يمكنك إنشاء نسخة احتياطية الآن، أو الإغلاق مباشرة دون نسخ احتياطي.",
      });

      if (choice.response === 2) {
        return;
      }

      if (choice.response === 0) {
        try {
          await requestBackupBeforeExit();
        } catch (error) {
          const errorChoice = await dialog.showMessageBox(mainWindow, {
            type: "warning",
            buttons: ["إغلاق بدون نسخة احتياطية", "إلغاء"],
            defaultId: 1,
            cancelId: 1,
            noLink: true,
            title: APP_TITLE,
            message: "تعذر إنشاء النسخة الاحتياطية قبل الإغلاق.",
            detail: error.message,
          });

          if (errorChoice.response !== 0) {
            return;
          }
        }
      }

      isQuitting = true;
      app.quit();
    } finally {
      isHandlingClosePrompt = false;
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  mainWindow.loadURL(targetUrl);
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

function resolvePythonCommand() {
  const venvPython = path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe");
  if (fs.existsSync(venvPython)) {
    return { command: venvPython, prefixArgs: [] };
  }

  const rootPython = path.join(PROJECT_ROOT, "python.exe");
  if (fs.existsSync(rootPython)) {
    return { command: rootPython, prefixArgs: [] };
  }

  return process.platform === "win32"
    ? { command: "py", prefixArgs: ["-3"] }
    : { command: "python3", prefixArgs: [] };
}

function resolveBackendLaunch(port) {
  if (app.isPackaged) {
    const packagedBackend = path.join(
      process.resourcesPath,
      "backend",
      BACKEND_DIST_NAME,
      BACKEND_EXE_NAME
    );

    if (!fs.existsSync(packagedBackend)) {
      throw new Error(`تعذر العثور على الباك إند المجمّع: ${packagedBackend}`);
    }

    return {
      command: packagedBackend,
      args: ["--host", "127.0.0.1", "--port", String(port)],
      cwd: path.dirname(packagedBackend),
    };
  }

  const python = resolvePythonCommand();
  return {
    command: python.command,
    args: [...python.prefixArgs, RUN_APP_PY, "--host", "127.0.0.1", "--port", String(port)],
    cwd: PROJECT_ROOT,
  };
}

function waitForServer(url, timeoutMs = 45000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const request = http.get(url, (response) => {
        response.resume();
        if (response.statusCode && response.statusCode < 500) {
          resolve();
          return;
        }
        retry();
      });

      request.on("error", retry);
      request.setTimeout(2500, () => {
        request.destroy();
        retry();
      });
    };

    const retry = () => {
      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error("انتهت مهلة انتظار تشغيل Django المحلي."));
        return;
      }
      setTimeout(check, 450);
    };

    check();
  });
}

function requestDesktopBackup(pathname, payload = {}) {
  return new Promise((resolve, reject) => {
    if (!appPort) {
      reject(new Error("تعذر تحديد منفذ الخادم المحلي."));
      return;
    }

    const requestBody = JSON.stringify(payload);
    const request = http.request(
      {
        hostname: "127.0.0.1",
        port: appPort,
        path: pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(requestBody),
          "X-Desktop-App": "1",
        },
      },
      (response) => {
        let responseBody = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          responseBody += chunk;
        });
        response.on("end", () => {
          let payload = null;
          if (responseBody) {
            try {
              payload = JSON.parse(responseBody);
            } catch (error) {
              reject(new Error("تعذر قراءة استجابة النسخ الاحتياطي من الخادم المحلي."));
              return;
            }
          }

          if (response.statusCode && response.statusCode >= 200 && response.statusCode < 300 && payload?.ok) {
            resolve(payload);
            return;
          }

          reject(new Error(payload?.message || "فشلت عملية النسخ الاحتياطي قبل الإغلاق."));
        });
      }
    );

    request.on("error", () => {
      reject(new Error("تعذر الاتصال بالخادم المحلي لتنفيذ النسخ الاحتياطي."));
    });

    request.setTimeout(15000, () => {
      request.destroy();
      reject(new Error("انتهت مهلة انتظار النسخ الاحتياطي قبل الإغلاق."));
    });

    request.end(requestBody);
  });
}

function requestBackupBeforeExit() {
  return requestDesktopBackup("/desktop/backup-before-exit/", {
    targetDirectory: getPreferredBackupDirectory(),
  });
}

async function chooseBackupDirectory() {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "اختر مجلد حفظ النسخة الاحتياطية",
    defaultPath: getPreferredBackupDirectory() || app.getPath("documents"),
    properties: ["openDirectory", "createDirectory"],
    buttonLabel: "اختيار المجلد",
  });

  if (result.canceled || !result.filePaths.length) {
    return null;
  }

  const selectedDirectory = result.filePaths[0];
  setPreferredBackupDirectory(selectedDirectory);
  return selectedDirectory;
}

async function chooseBackupDirectoryAndCreate() {
  const selectedDirectory = await chooseBackupDirectory();
  if (!selectedDirectory) {
    return { canceled: true };
  }

  const backupResult = await requestDesktopBackup("/desktop/backup/create/", {
    targetDirectory: selectedDirectory,
  });

  return {
    canceled: false,
    preferredDirectory: selectedDirectory,
    ...backupResult,
  };
}

async function createBackupInPreferredDirectory() {
  const preferredDirectory = getPreferredBackupDirectory();
  const backupResult = await requestDesktopBackup("/desktop/backup/create/", {
    targetDirectory: preferredDirectory,
  });

  return {
    canceled: false,
    preferredDirectory,
    ...backupResult,
  };
}

function startDjangoServer(port) {
  const backend = resolveBackendLaunch(port);

  djangoProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    env: {
      ...process.env,
      DJANGO_SETTINGS_MODULE: "brandregistry.settings",
      DESKTOP_LOCAL_MODE: "1",
      DJANGO_DEBUG: process.env.DJANGO_DEBUG ?? "0",
      APP_HOST: "127.0.0.1",
      APP_PORT: String(port),
      PYTHONUNBUFFERED: "1",
      BROWSER: "none",
    },
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  djangoProcess.stdout.on("data", (data) => {
    process.stdout.write(`[django] ${data}`);
  });

  djangoProcess.stderr.on("data", (data) => {
    process.stderr.write(`[django] ${data}`);
  });

  djangoProcess.on("exit", (code) => {
    if (!isQuitting && code !== 0 && !bootstrapErrorShown) {
      bootstrapErrorShown = true;
      dialog.showErrorBox(
        APP_TITLE,
        `توقف خادم Django المحلي بشكل غير متوقع. رمز الخروج: ${code ?? "غير معروف"}.`
      );
      app.quit();
    }
  });
}

function stopDjangoServer() {
  if (!djangoProcess || djangoProcess.killed) {
    return;
  }

  const pid = djangoProcess.pid;
  if (!pid) {
    return;
  }

  if (process.platform === "win32") {
    execFile("taskkill", ["/pid", String(pid), "/T", "/F"], { windowsHide: true }, () => {});
  } else {
    djangoProcess.kill("SIGTERM");
  }
}

async function bootstrap() {
  appPort = await findFreePort();
  const appUrl = `http://127.0.0.1:${appPort}/`;
  const healthUrl = `${appUrl}healthz/`;
  startDjangoServer(appPort);
  await waitForServer(healthUrl);
  createMainWindow(appUrl);
}

async function runDesktopApp() {
  Menu.setApplicationMenu(null);
  createSplashWindow();

  try {
    await bootstrap();
  } catch (error) {
    bootstrapErrorShown = true;
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    dialog.showErrorBox(
      APP_TITLE,
      [
        "تعذر تشغيل Django داخل Electron.",
        "",
        error.message,
        "",
        "تأكد من وجود Python والبيئة الافتراضية ومن تثبيت متطلبات المشروع.",
      ].join("\n")
    );
    app.quit();
  }
}

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.focus();
    }
  });
}

app.whenReady().then(runDesktopApp);

ipcMain.handle("desktop-backup:create-in-preferred-directory", async () => createBackupInPreferredDirectory());
ipcMain.handle("desktop-backup:choose-and-create", async () => chooseBackupDirectoryAndCreate());
ipcMain.handle("desktop-backup:get-preferred-directory", async () => getPreferredBackupDirectory());
ipcMain.handle("desktop-backup:clear-preferred-directory", async () => {
  clearPreferredBackupDirectory();
  return { ok: true };
});

app.on("before-quit", () => {
  isQuitting = true;
  stopDjangoServer();
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0 && appPort) {
    createMainWindow(`http://127.0.0.1:${appPort}/`);
  }
});
