# Dwine patch notes

## Unreleased

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
