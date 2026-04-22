const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktopApp", {
  platform: process.platform,
  versions: {
    chrome: process.versions.chrome,
    electron: process.versions.electron,
    node: process.versions.node,
  },
  createBackupInPreferredDirectory: () => ipcRenderer.invoke("desktop-backup:create-in-preferred-directory"),
  chooseBackupDirectoryAndCreate: () => ipcRenderer.invoke("desktop-backup:choose-and-create"),
  getPreferredBackupDirectory: () => ipcRenderer.invoke("desktop-backup:get-preferred-directory"),
  useDefaultBackupDirectory: () => ipcRenderer.invoke("desktop-backup:clear-preferred-directory"),
});
