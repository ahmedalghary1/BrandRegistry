const { app, BrowserWindow, Menu, dialog } = require("electron");
const { execFile, spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const path = require("path");

const APP_TITLE = "نظام إدارة العلامات والنماذج الصناعية";
const PROJECT_ROOT = path.resolve(__dirname, "..");
const MANAGE_PY = path.join(PROJECT_ROOT, "manage.py");
const SPLASH_HTML = path.join(__dirname, "splash.html");
const ICON_PATH = path.join(PROJECT_ROOT, "static", "dashboard_files", "logo-gold.png");

let djangoProcess = null;
let mainWindow = null;
let splashWindow = null;
let appPort = null;
let isQuitting = false;
let bootstrapErrorShown = false;

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

function startDjangoServer(port) {
  const python = resolvePythonCommand();
  const args = [
    ...python.prefixArgs,
    MANAGE_PY,
    "runserver",
    `127.0.0.1:${port}`,
    "--noreload",
  ];

  djangoProcess = spawn(python.command, args, {
    cwd: PROJECT_ROOT,
    env: {
      ...process.env,
      DJANGO_SETTINGS_MODULE: "brandregistry.settings",
      DESKTOP_LOCAL_MODE: "1",
      DJANGO_DEBUG: process.env.DJANGO_DEBUG ?? "0",
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
  startDjangoServer(appPort);
  await waitForServer(appUrl);
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
