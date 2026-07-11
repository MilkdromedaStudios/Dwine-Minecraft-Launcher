# Dwine patch notes

## Unreleased

**A polished client, not a hack client**
- Replaced the ClickGUI with a modern **tile select menu** (Right Shift): a card
  per module with iOS-style toggles, category tabs, a scrollable grid and a
  per-module settings sheet (sliders, toggles, mode pickers, key binds).
- Added **custom sleek buttons** — a mixin restyles every vanilla button
  (title, pause, options…) into rounded, accented buttons, leaving icon buttons
  untouched.
- Dropped the "arraylist" HUD (the clearest hack-client tell). Real
  in-game screenshots + a demo reel captured from `./gradlew runClient` were
  added to the README.

**The features are a real mod now**
- Dwine's in-game features ship as an actual Fabric client mod
  (`mod/`, Minecraft 26.x, Java 25) instead of a config file waiting for a
  companion that never existed. It has a sleek custom UI — a flat, translucent,
  draggable **ClickGUI** (Right Shift) with per-category panels, module toggles,
  expandable settings and rebindable keys, plus a drag-and-drop **HUD editor**
  (Right Ctrl, scroll to scale).
- Many legit, server-legal client modules: HUD (FPS, CPS, coordinates,
  direction, ping, clock, keystrokes, armour, potions, session timer, speed,
  biome, watermark, active-module list), Render (Fullbright, Zoom, No Bobbing,
  FOV changer), Movement (Toggle Sprint, Toggle Sneak, Auto Sprint) and Misc
  (Frame Limit). Everything is client-side and cosmetic/QoL — no packets, no
  injection, nothing the server can see.
- **GitHub Actions builds the mod** (`.github/workflows/build-mod.yml`): every
  push builds `dwine-client-<version>.jar` as an artifact, and tagging `v*`
  attaches it to the release.
- **The launcher stays in Python and launches the game with the mod.** On Play,
  Fabric/Quilt profiles on a supported version get the Dwine jar dropped into
  `mods/` (Fabric API installed alongside), and the launcher writes the shared
  `config/dwine/features.json` the mod reads. New CLI: `dwine client status |
  install | features | enable <name> | disable <name> --profile <p>`.

**Login without Azure — link code**
- New default sign-in: click **Sign in with Microsoft**, enter a short code
  at microsoft.com/link, done. Uses the official Minecraft launcher's public
  client ID against Microsoft's official device-code endpoints — no Azure
  account, no app registration, no setup. (CLI: `dwine login`.)
- Your own Azure app still works: paste its client ID under
  *Accounts → Advanced* (or `dwine login --client-id <ID>`) and Dwine uses
  it instead. Existing Azure-flow accounts keep refreshing as before.

**Modrinth actually matches your game version now**
- Profiles set to "Latest release" previously searched and installed mods
  with **no version filter at all**, so the newest build won even when it
  was for a different Minecraft version — installs then crashed or silently
  didn't load. "Latest release" now resolves to the real version id before
  every search, install and update.
- `dwine mods search` no longer returns nothing for vanilla-loader profiles
  (it sent `categories:vanilla` as a Modrinth facet).

**A real mod manager**
- The Mods & Packs page now shows what's installed per profile — including
  jars you dropped into `mods/` yourself — with Remove and Update All next
  to search/install. Resource packs and shaders get the same treatment.

**Back to basics**
- The launcher is now just: Home (version chooser + Play), Mods & Packs,
  Logs, Accounts, Settings. The feature catalog, HUD editor, crosshair
  drawpad, screenshots gallery, news feed, in-game theme pack, Discord/
  Spotify/cosmetics integrations and settings sync are gone — client mods
  from Modrinth are the feature system.

**Login that actually works**
- Fixed the Microsoft device-code prompt never appearing (it was updated from
  a worker thread); the code now shows up and your browser opens automatically
- The Azure client-ID setup is built into the Accounts page (and
  `dwine login --client-id <ID>`) with step-by-step instructions — before,
  login could not work at all without hand-editing settings.json
- Fixed newly added accounts being invisible to the Play button until restart
- Clearer errors for rejected client IDs, expired codes and declined sign-ins

**Version chooser**
- Pick any Minecraft version ever shipped — releases, snapshots, old
  beta/alpha — plus the loader (Vanilla/Fabric/Quilt/Forge), right on Home
- New-profile dialog: name + version + loader. Preset profiles are gone

**100+ built-in client features, each with settings**
- The whole catalog: ToggleSprint/ToggleSneak, keystrokes, CPS/FPS/ping/
  coordinates/clock/compass/armor/potion/direction/speed/stopwatch HUDs,
  combo counter, hit delay + hit distance displays, entity/block hitboxes,
  block outline/overlay/highlight, chunk borders, light overlay, mob health
  and nameplates, trajectories, damage tint/particles, swing + old
  animations, wavey capes/skins, crosshair animations & movement, chat
  (transparency, size sliders, animations, filter, timestamps, heads),
  better tab, AutoGG, scoreboard/bossbar/hotbar customizers, inventory/menu
  blur + animations, menu shader, zoom, smooth camera, fullbright + gamma,
  time changer, weather toggle, fps graph, chunk graph, culling (entity/
  particle/chunk), shadow/VSync/AA/mipmap/fog toggles, render + entity
  distance sliders, custom fonts, custom colors, and more
- Every feature exposes its own settings (⚙): sliders, colors, choices,
  keys — saved per feature and written to `config/dwine/features.json` at
  launch for the companion mod to render **in game**
- The in-game HUD editor is a feature too (moveable HUD, scaling, opacity,
  backgrounds, editor key)

**Crosshair drawpad**
- Paint a pixel-perfect custom crosshair (left-click paint, right-click
  erase, palette + custom colors, shape starting points, 11–31 px canvases);
  it renders into the theme resource pack like any other crosshair

**Modrinth GUI fixed**
- Search/install no longer dead-ends when no profile exists (a default
  profile is created automatically) and the profile list refreshes when the
  page is shown instead of only at startup
- Errors now surface as toasts, results/installs give status feedback,
  double-click installs

**Launcher**
- Presets removed everywhere (UI and CLI) — the launcher stays minimal:
  themes, profiles, accounts; the features live in the game
- `dwine setup-path` no longer crashes (a duplicate function shadowed the
  real PATH instructions) and the README gained an exact per-OS PATH guide

## 0.1.0 — first public build

**Launcher**
- Full version support: Vanilla, Fabric, Quilt and Forge, from 1.0 to the latest snapshot
- Microsoft account login (official device-code flow), multi-account switching
- Isolated profiles with one-click presets: FPS, PvP, Skyblock, Cinematic
- Managed Java runtimes (Temurin) — the right Java per version, automatically
- One-click quick-join, crash analyzer, news panel, patch notes, logs viewer
- Profile export/import and file-based settings sync

**Content**
- Modrinth-powered mod, resource pack and shader managers with sha512 verification
- Dependency resolution, one-click updates, per-version compatibility matching
- Performance preset: Sodium, Lithium, FerriteCore, Entity Culling, ModernFix,
  ImmediatelyFast, Krypton, Dynamic FPS, C2ME, Memory Leak Fix, Starlight (older versions)

**Client experience**
- Theme engine with six built-in themes (Dark, Light, Neon, Minimal, Glass, Ember)
- In-game theming via the generated "Dwine Theme" resource pack — buttons, hotbar,
  menus and crosshair, on every version, 100% server-legal
- Drag-and-drop HUD editor with nine-anchor scaling layouts
- Parametric crosshair editor with six presets
- Screenshot gallery + editor, server ping tester, Discord Rich Presence,
  Spotify miniplayer, free cosmetic capes

**Safety**
- The safety policy engine ships in this build and is not configurable:
  automation is singleplayer-only, radar-like tools switch to fair-play variants
  on competitive networks, and nothing ever touches packets or gameplay.
