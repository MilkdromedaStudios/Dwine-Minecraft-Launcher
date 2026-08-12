const $ = (id) => document.getElementById(id);
const toast = $('toast');

function notify(message, error = false) {
  toast.textContent = message;
  toast.className = `toast show${error ? ' error' : ''}`;
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => toast.className = 'toast', 3500);
}

async function refresh() {
  const state = await window.dwine.getState();
  $('statusText').textContent = state.minecraftPresent ? 'Ready' : 'Minecraft Launcher needed';
  $('statusDot').style.background = state.minecraftPresent ? '#3bd56f' : '#f0a04b';
  $('runtimeText').textContent = `Minecraft ${state.targetVersion} · Fabric${state.lastLoaderVersion ? ' ' + state.lastLoaderVersion : ''}`;
  $('jarLabel').textContent = state.selectedModJar ? state.selectedModJar.split(/[\\/]/).pop() : 'Select 26.2 jar';
}

async function prepare() {
  try {
    notify('Preparing Dwine 26.2…');
    const result = await window.dwine.prepare();
    notify(`Ready: Fabric ${result.loaderVersion}`);
    await refresh();
  } catch (e) {
    notify(e.message || String(e), true);
  }
}

async function launch() {
  try {
    notify('Preparing and opening Minecraft Launcher…');
    await window.dwine.launch();
    notify('Minecraft Launcher opened. Choose the Dwine 26.2 installation and press Play.');
    await refresh();
  } catch (e) {
    notify(e.message || String(e), true);
  }
}

$('playNow').addEventListener('click', launch);
$('rowLaunch').addEventListener('click', launch);
$('prepare').addEventListener('click', prepare);
$('manageMods').addEventListener('click', async () => {
  const state = await window.dwine.chooseModJar();
  if (state) {
    notify('Dwine mod jar selected.');
    await refresh();
  }
});
$('minimize').addEventListener('click', () => window.dwine.windowMinimize());
$('maximize').addEventListener('click', () => window.dwine.windowMaximize());
$('close').addEventListener('click', () => window.dwine.windowClose());

document.querySelectorAll('.nav:not(.active)').forEach(btn => btn.addEventListener('click', () => notify(`${btn.textContent.trim()} will use Dwine's local registry in the next UI pass.`)));
refresh().catch(e => notify(e.message || String(e), true));
