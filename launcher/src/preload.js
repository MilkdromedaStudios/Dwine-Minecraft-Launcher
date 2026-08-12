const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('dwine', {
  getState: () => ipcRenderer.invoke('dwine:get-state'),
  chooseModJar: () => ipcRenderer.invoke('dwine:choose-mod-jar'),
  prepare: () => ipcRenderer.invoke('dwine:prepare'),
  launch: () => ipcRenderer.invoke('dwine:launch'),
  openFolder: (kind) => ipcRenderer.invoke('dwine:open-folder', kind),
  saveSettings: (patch) => ipcRenderer.invoke('dwine:save-settings', patch),
  windowMinimize: () => ipcRenderer.send('dwine:window-minimize'),
  windowMaximize: () => ipcRenderer.send('dwine:window-maximize'),
  windowClose: () => ipcRenderer.send('dwine:window-close')
});
