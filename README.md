<p align="center">
  <img src="assets/logo.svg" alt="Dwine" width="420"/>
</p>

<h3 align="center">The fully legitimate, next-generation Minecraft client + launcher.</h3>

<p align="center">
  Python-powered · Every version · Vanilla / Fabric / Quilt / Forge · 100% non-bannable by design
</p>

<p align="center">
  <img alt="python" src="https://img.shields.io/badge/python-3.10%2B-4F8CFF">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-3DDC97">
  <img alt="platforms" src="https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-B18CFF">
  <img alt="policy" src="https://img.shields.io/badge/cheats-none%2C%20ever-FF5D73">
</p>

---

Dwine is what a client looks like when *"never get banned"* is an engineering
constraint instead of a marketing line. It launches every Minecraft version,
installs a curated performance stack matched to your exact version, reskins
Minecraft's own UI through an auto-generated resource pack, and wraps it all
in a launcher that's genuinely pleasant to look at.

![Dwine home](assets/screenshots/home-dark.png)

## Why Dwine over Lunar?

| | Dwine | Typical "client" |
|---|---|---|
| **Version support** | Every version, all four loaders (Vanilla, Fabric, Quilt, Forge) | A handful of fixed versions |
| **In-game theming** | Your theme rendered into a server-legal resource pack | Injected code you can't audit |
| **Mod source** | Official Modrinth API, sha512-verified, open source mods | Rehosted, repackaged binaries |
| **Safety** | Policy engine *in code* — automation can't run on servers even if you try | "Trust us" |
| **Extensibility** | Documented Python plugin API | Closed |
| **Cosmetics** | Free | Paid |
| **The launcher itself** | Open Python you can read in an afternoon | Closed |

## Feature tour

### 🎨 UI & theming — outside *and inside* the game
- The launcher itself stays minimal: **themes, profiles, accounts — no preset bloat**. The features live in the game, not in launcher menus
- Six built-in themes — **Dwine Dark, Light, Neon, Minimal, Glass, Ember** — plus JSON custom themes with gradients, glass panels and animated accents
- **In-game theming with zero injection**: on every launch Dwine renders your theme into the `Dwine Theme` resource pack — buttons, hotbar, menu backgrounds and crosshair — legal on every server, working on every version (legacy `widgets.png` *and* modern 1.20.2+ sprites with nine-slice metadata)
- **Drag-and-drop HUD editor** with nine-anchor snapping — in the launcher *and* in game (companion mod, `RSHIFT` by default)
- **Crosshair drawpad**: paint your own crosshair pixel by pixel (plus parametric shapes as starting points), rendered into the theme pack

![In-game widgets](assets/screenshots/ingame-widgets.png)
*The same three themes rendered as in-game button/hotbar textures by `dwine theme build`.*

### ⚡ Performance
- **One-click FPS stack**, resolved against your exact version and loader: Sodium · Lithium · FerriteCore · Entity Culling · ModernFix · ImmediatelyFast · Krypton · Dynamic FPS · Memory Leak Fix · Starlight *(older versions)* · C2ME multi-threaded chunk loading
- Iris shader pipeline with one-click shader packs
- Managed Java runtimes (Temurin) — the right JVM per version, automatically
- Auto-cleaner for logs, crash reports and download caches with a size budget
- Parallel, checksum-verified downloads for versions, libraries and assets

### 🧩 100+ built-in features (all legit, all with settings)
Every toggle is cosmetic or quality-of-life — information display, comfort,
style — and **every feature has its own settings** (the ⚙ button next to
each toggle): sliders, colors, styles, keybinds. All of it is written into
the profile's `config/dwine/` at launch and rendered **in game** by the
companion mod — the launcher is just the remote control.

**HUD** Keystrokes (colors, mouse/spacebar, CPS-on-keys) · FPS counter · CPS counter · ping display · coordinates (Nether-converted, biome) · clock (real/in-game) · compass ribbon · armor HUD · potion HUD · direction HUD · speed HUD · stopwatch · combo counter · hit delay indicator · block hit delay · hit distance display · saturation (AppleSkin) · server info · match timer · memory/session stats · FPS graph · chunk graph
**Visual** custom crosshair + drawpad · crosshair animations & movement · entity/block hitboxes (thickness + color sliders) · better block outline (thickness, color, style) · block selection highlight · block overlay · block break overlay · chunk borders · light overlay · mob health & nameplates · arrow trajectories & projectile path (auto-off on competitive) · hit color · damage tint · damage particles · better particles (amount slider) · swing/old animations · wavey capes & skins · motion blur · cooldown indicator · custom fonts · custom colors · item physics
**Chat** transparent chat (opacity sliders) · chat scale/width/height sliders · chat animations · chat filter · time stamps · chat heads · better tab list · AutoGG
**Interface** in-game HUD editor (moveable everything, scale + opacity + backgrounds) · scoreboard customizer (+position) · bossbar customizer (+position) · hotbar customizer (+position) · inventory blur & animations · menu blur · menu shader
**Utility** ToggleSprint · ToggleSneak · zoom · smooth camera · fullbright + gamma slider · time changer (visual) · weather toggle · minimap + waypoints · skip death screen · friend guard · screenshot manager · replay (Replay Mod)
**Performance** FPS boost stack · memory cleaner · entity/particle/chunk culling · shadow toggle · VSync toggle · anti-aliasing · mipmap slider · fog toggle · render distance & simulation sliders · entity distance slider · animation toggles · dynamic FPS · multi-threaded chunks · Iris shaders
**Hypixel** Skyblock utilities (waypoints, dungeon map, timers, trackers) · level head · Bedwars timers · nick hider · party HUD
**Media** Spotify miniplayer · Discord Rich Presence · free cosmetic capes

![Features](assets/screenshots/features-ember.png)

### 🧭 The launcher
- Microsoft login via the official device-code flow (your password never touches Dwine), multi-account switching, automatic token refresh — with the Azure client-ID setup built into the Accounts page
- **Version chooser**: every Minecraft version ever shipped — releases, snapshots, old beta/alpha — with a loader picker (Vanilla / Fabric / Quilt / Forge), right on the Home tab
- Isolated **profiles** — each with its own mods, packs, shaders and worlds. No presets: you pick the name, version and loader
- Mod / resource pack / shader managers with Modrinth search, one-click install, dependency resolution and **Update All**
- One-click server join, server ping tester (a real Server List Ping implementation)
- Crash analyzer that turns stack traces into plain-English fixes
- News panel, patch notes, screenshot gallery + editor, live logs viewer
- Profile export/import and file-based settings sync (Dropbox/Drive/Syncthing — no Dwine account needed)
- Plugin API: drop a `.py` file in the plugins folder to add commands, hooks and UI pages

![Settings](assets/screenshots/settings-glass.png)

## 🔒 The safety model (read this)

Dwine's core promise is enforced by `dwine/features/safety.py`, not by a
settings page:

1. **No cheats exist in the codebase.** No packet manipulation, no movement or
   combat modification, no server-visible behavior changes. The feature catalog
   is audited by the test suite (`dwine safety` runs the same audit).
2. **Input automation is singleplayer-only — enforced.** The auto clicker is
   disabled *at launch time* for any multiplayer target, whatever your settings
   say. This is deliberately not configurable.
3. **Fair-play variants on competitive networks.** Joining Hypixel & friends
   automatically swaps radar-like tools (cave map, entity radar) for their
   fair-play builds.
4. **Nothing is injected into the game.** In-game theming is a resource pack;
   features are vetted open-source mods installed from Modrinth or config read
   by the companion mod. Resource packs and these mods are permitted by
   Hypixel's allowed-modifications policy — but rules change, so the policy
   engine is updateable and conservative by default.

> ⚠️ No client can promise more than its own behavior: always follow the rules
> of the server you play on. Dwine's job is to make the compliant path the
> only path.

## 📦 Installation

**Requirements:** Python 3.10+ · that's it. (Dwine manages Java for you.)

```bash
# 1. Install Dwine with the UI, theming and Discord extras
pip install "dwine[full] @ git+https://github.com/MilkdromedaStudios/Dwine"

# 2. Ensure the `dwine` command is available, then open the launcher
python -m dwine setup-path
dwine
```

From source instead:

```bash
git clone https://github.com/MilkdromedaStudios/Dwine
cd Dwine
pip install -e ".[full]"
python -m dwine setup-path
dwine
```

### Making `dwine` work in your terminal

`python -m dwine setup-path` installs a tiny launcher script (a "shim")
into a per-user folder and prints its exact location. If typing `dwine`
already works afterwards, you're done. If your terminal says
`dwine: command not found`, that folder isn't on your PATH yet — add it
once and it works forever:

**Where the shim lives**

| System | Shim file | Folder to put on PATH |
| --- | --- | --- |
| Windows | `%APPDATA%\Python\Scripts\dwine.cmd` | `%APPDATA%\Python\Scripts` |
| macOS / Linux | `~/.local/bin/dwine` | `$HOME/.local/bin` |

**Windows (GUI, recommended)**

1. Press the Windows key, type *"environment variables"*, open
   **Edit the system environment variables** → **Environment Variables…**
2. Under **User variables**, select `Path` → **Edit** → **New**.
3. Paste `%APPDATA%\Python\Scripts` and press **OK** on every dialog.
4. Close and reopen your terminal, then run `dwine --version`.

**Windows (PowerShell one-liner)**

```powershell
[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';' + $env:APPDATA + '\Python\Scripts', 'User')
```

Then open a *new* terminal window.

**macOS (zsh — the default shell)**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
dwine --version
```

**Linux (bash)**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
dwine --version
```

**Troubleshooting**

- Nothing happens / old version runs → a *new* terminal window is required
  after editing PATH; already-open windows keep the old value.
- `python -m dwine` works but `dwine` doesn't → the PATH entry is missing or
  misspelled; run `python -m dwine setup-path` again, it prints the exact
  folder and line to add.
- Multiple Pythons installed → the shim pins the Python that installed
  Dwine, so it keeps working even if `python` later points somewhere else.

### First run

1. **Accounts → Login setup** — paste your (free) Azure app client ID.
   Microsoft requires every launcher to bring its own; the Accounts page
   walks you through the ~5-minute registration, or see the docstring in
   [`dwine/launcher/auth.py`](dwine/launcher/auth.py). Then
   **Add Microsoft account** — your browser opens with a code, and the
   launcher finishes by itself. (CLI: `dwine login --client-id <ID>`.)
2. **Home** — pick any Minecraft version and loader in the version chooser
   (or **+ New profile** for a fresh one — name, version, loader, done).
3. **Play.** Dwine installs the version, loader, mods and theme pack, then
   launches.

### Headless / CLI

Everything works without a display:

```bash
dwine versions                          # list Minecraft versions
dwine versions --snapshots --old        # …including snapshots + beta/alpha
dwine install 1.21.1 --loader fabric    # install any version + loader
dwine login --client-id <AZURE_ID>      # save your client ID + device login
dwine launch my-profile --server play.example.com
dwine mods search sodium --profile my-profile
dwine theme set neon                    # six built-in themes
dwine theme build neon --mc 1.21       # render the in-game pack anywhere
dwine ping mc.hypixel.net               # real SLP ping tester
dwine clean --apply                     # sweep logs/caches
dwine crash my-profile                  # analyze the last crash
dwine safety                            # run the feature-catalog audit
dwine sync push                         # settings snapshot to your sync folder
dwine update --check                    # check GitHub for a Dwine release
dwine update                            # install the newest Dwine release
dwine setup-path                        # repair/install the dwine command shim
```

## 🏗 Architecture

```
dwine/
├── core/          settings JSON system · event bus · HTTP w/ sha verification
├── launcher/      Mojang manifest · installer · Fabric/Quilt/Forge · MS auth
│                  profiles · Java runtimes · crash analyzer · news · updates
├── content/       Modrinth client · mod/pack/shader managers
├── features/      feature catalog · SAFETY POLICY · HUD model · crosshair
├── theme/         theme definitions · Qt stylesheet engine · in-game pack gen
├── ui/            PySide6 launcher (custom widgets, 9 pages)
├── integrations/  Discord RPC · Spotify (PKCE) · settings sync · cosmetics
├── tools/         auto-cleaner · SLP ping · screenshots · skin changer
└── plugins/       plugin loader + stable API
```

Design rules that keep it honest:

- **Modular**: every subsystem is importable and usable without the UI.
- **No rehosting**: content comes from official APIs (Mojang, Modrinth,
  Fabric/Quilt/Forge, Adoptium) with checksums verified locally.
- **User data is sacred**: worlds, configs and screenshots are never cleanup
  candidates; tokens never leave the machine and are excluded from sync.
- **Plugins can't touch the game process** — they extend the launcher only.

## 🧪 Development

```bash
pip install -e ".[dev]"
python -m pytest          # 36 tests, offline, < 1s
dwine safety              # the audit that gates every release
```

Contributions welcome — mods proposed for the catalog must be open source,
Modrinth-hosted, and compliant with the safety model (see
`dwine/features/registry.py` for the metadata a feature needs).

## FAQ

**Is this really non-bannable?**
Dwine only ever does three things to your game: launch it (like any launcher),
install vetted open-source mods (the same ones millions use), and apply a
resource pack. The risky category — automation — is locked to singleplayer in
code. Follow your server's rules and you're fine.

**Does it work with [my version]?**
Yes. The installer speaks Mojang's official metadata, so everything from 1.0
to the latest snapshot installs — with Fabric, Quilt and Forge wherever those
loaders support the version.

**Where's the "companion mod"?**
Features marked *companion* in the catalog (custom HUD rendering, item resize,
capes, party HUD…) are configured by the launcher and rendered by the Dwine
companion Fabric mod, which lives in its own repo and is being upstreamed.
Everything else in this README works today from this repo alone.

**Why do I need my own Azure client ID?**
Microsoft requires each launcher deployment to register (free) for the login
API. It takes ~5 minutes, once, and means your auth traffic is yours alone.

---

<p align="center">
MIT © Milkdromeda Studios ·
<a href="CHANGELOG.md">Patch notes</a> ·
<a href="examples/plugins/server_status.py">Plugin example</a>
</p>
