const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');
const { spawn } = require('child_process');

const MC_VERSION = '26.2';
const PROFILE_NAME = 'Dwine 26.2';

function mcDir() {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'), '.minecraft');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'minecraft');
  return path.join(os.homedir(), '.minecraft');
}

function bundledModJar() {
  if (app.isPackaged) return path.join(process.resourcesPath, 'dwine', 'dwine-26.2.jar');
  return path.join(__dirname, '..', 'bundled', 'dwine-26.2.jar');
}

function dataFile() { return path.join(app.getPath('userData'), 'dwine-launcher.json'); }
function readState() {
  try { return JSON.parse(fs.readFileSync(dataFile(), 'utf8')); }
  catch { return { selectedModJar: '', lastLoaderVersion: '', theme: 'dark', instanceName: PROFILE_NAME }; }
}
function writeState(next) {
  fs.mkdirSync(path.dirname(dataFile()), { recursive: true });
  fs.writeFileSync(dataFile(), JSON.stringify(next, null, 2));
  return next;
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'DwineLauncher/0.3' } }, res => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) return resolve(getJson(res.headers.location));
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => {
        if (res.statusCode < 200 || res.statusCode >= 300) return reject(new Error(`HTTP ${res.statusCode}: ${url}`));
        try { resolve(JSON.parse(body)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

function download(url, target) {
  return new Promise((resolve, reject) => {
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const file = fs.createWriteStream(target);
    const request = https.get(url, { headers: { 'User-Agent': 'DwineLauncher/0.3' } }, res => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        file.close(); fs.rmSync(target, { force: true });
        return resolve(download(res.headers.location, target));
      }
      if (res.statusCode !== 200) return reject(new Error(`Download failed: HTTP ${res.statusCode}`));
      res.pipe(file);
      file.on('finish', () => file.close(resolve));
    });
    request.on('error', err => { file.close(); fs.rmSync(target, { force: true }); reject(err); });
  });
}

function walkForJava(root, depth = 0) {
  if (!root || !fs.existsSync(root) || depth > 7) return null;
  let entries;
  try { entries = fs.readdirSync(root, { withFileTypes: true }); } catch { return null; }
  const javaName = process.platform === 'win32' ? 'javaw.exe' : 'java';
  for (const entry of entries) {
    const full = path.join(root, entry.name);
    if (entry.isFile() && entry.name.toLowerCase() === javaName.toLowerCase()) return full;
  }
  for (const entry of entries) {
    if (entry.isDirectory()) {
      const hit = walkForJava(path.join(root, entry.name), depth + 1);
      if (hit) return hit;
    }
  }
  return null;
}

function findJava() {
  const runtime = walkForJava(path.join(mcDir(), 'runtime'));
  if (runtime) return runtime;
  return process.platform === 'win32' ? 'javaw.exe' : 'java';
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    child.stderr.on('data', d => stderr += d.toString());
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve() : reject(new Error(stderr || `${command} exited with ${code}`)));
  });
}

async function installFabric() {
  const loaders = await getJson(`https://meta.fabricmc.net/v2/versions/loader/${MC_VERSION}`);
  if (!Array.isArray(loaders) || loaders.length === 0) throw new Error(`Fabric does not currently publish a loader for Minecraft ${MC_VERSION}.`);
  const loaderVersion = loaders.find(x => x.loader && x.loader.stable)?.loader?.version || loaders[0].loader.version;
  const installers = await getJson('https://meta.fabricmc.net/v2/versions/installer');
  const installerVersion = installers.find(x => x.stable)?.version || installers[0]?.version;
  if (!installerVersion) throw new Error('Could not resolve a Fabric installer version.');
  const cache = path.join(app.getPath('userData'), 'cache');
  const installerJar = path.join(cache, `fabric-installer-${installerVersion}.jar`);
  if (!fs.existsSync(installerJar)) {
    await download(`https://maven.fabricmc.net/net/fabricmc/fabric-installer/${installerVersion}/fabric-installer-${installerVersion}.jar`, installerJar);
  }
  await run(findJava(), ['-jar', installerJar, 'client', '-dir', mcDir(), '-mcversion', MC_VERSION, '-loader', loaderVersion, '-noprofile']);
  return loaderVersion;
}

function installDwineJar(customJar) {
  const source = customJar && fs.existsSync(customJar) ? customJar : bundledModJar();
  if (!source || !fs.existsSync(source)) throw new Error('The bundled Dwine 26.2 client mod is missing. Reinstall Dwine or choose a custom jar.');
  if (!path.basename(source).toLowerCase().endsWith('.jar')) throw new Error('The Dwine mod must be a .jar file.');
  const mods = path.join(mcDir(), 'mods');
  fs.mkdirSync(mods, { recursive: true });
  for (const file of fs.readdirSync(mods)) {
    if (/^dwine.*\.jar$/i.test(file)) fs.rmSync(path.join(mods, file), { force: true });
  }
  const target = path.join(mods, `dwine-${MC_VERSION}.jar`);
  fs.copyFileSync(source, target);
  return target;
}

function registerProfile(loaderVersion) {
  const profilePath = path.join(mcDir(), 'launcher_profiles.json');
  let profiles = { profiles: {} };
  try { profiles = JSON.parse(fs.readFileSync(profilePath, 'utf8')); } catch {}
  profiles.profiles ||= {};
  const versionId = `fabric-loader-${loaderVersion}-${MC_VERSION}`;
  profiles.profiles.dwine = {
    created: new Date().toISOString(),
    icon: 'Grass',
    lastUsed: new Date().toISOString(),
    lastVersionId: versionId,
    name: PROFILE_NAME,
    type: 'custom'
  };
  fs.mkdirSync(mcDir(), { recursive: true });
  fs.writeFileSync(profilePath, JSON.stringify(profiles, null, 2));
  return versionId;
}

async function prepare() {
  const state = readState();
  if (!fs.existsSync(mcDir())) throw new Error('Minecraft has not been initialized yet. Open the official Minecraft Launcher once first.');
  const loaderVersion = await installFabric();
  const modTarget = installDwineJar(state.selectedModJar);
  const versionId = registerProfile(loaderVersion);
  const next = writeState({ ...state, lastLoaderVersion: loaderVersion, lastPreparedAt: new Date().toISOString() });
  return { ok: true, loaderVersion, versionId, modTarget, bundled: !state.selectedModJar, state: next };
}

async function launchOfficialLauncher() {
  if (process.platform === 'win32') {
    await shell.openExternal('minecraft://');
    return;
  }
  throw new Error('The packaged Dwine launcher currently supports official-launcher handoff on Windows.');
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1536, height: 1024, minWidth: 1080, minHeight: 720,
    frame: false, backgroundColor: '#09111d',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  ipcMain.on('dwine:window-minimize', () => win.minimize());
  ipcMain.on('dwine:window-maximize', () => win.isMaximized() ? win.unmaximize() : win.maximize());
  ipcMain.on('dwine:window-close', () => win.close());
}

ipcMain.handle('dwine:get-state', async () => ({
  ...readState(),
  minecraftDir: mcDir(),
  minecraftPresent: fs.existsSync(mcDir()),
  targetVersion: MC_VERSION,
  bundledModPresent: fs.existsSync(bundledModJar())
}));
ipcMain.handle('dwine:save-settings', async (_e, patch) => writeState({ ...readState(), ...patch }));
ipcMain.handle('dwine:choose-mod-jar', async () => {
  const result = await dialog.showOpenDialog({ title: 'Choose custom Dwine 26.2 client mod', properties: ['openFile'], filters: [{ name: 'Java archive', extensions: ['jar'] }] });
  if (result.canceled || !result.filePaths[0]) return null;
  return writeState({ ...readState(), selectedModJar: result.filePaths[0] });
});
ipcMain.handle('dwine:use-bundled-mod', async () => writeState({ ...readState(), selectedModJar: '' }));
ipcMain.handle('dwine:prepare', async () => prepare());
ipcMain.handle('dwine:launch', async () => { await prepare(); await launchOfficialLauncher(); return { ok: true }; });
ipcMain.handle('dwine:open-folder', async (_e, kind) => {
  const target = kind === 'mods' ? path.join(mcDir(), 'mods') : mcDir();
  fs.mkdirSync(target, { recursive: true }); await shell.openPath(target); return target;
});

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
