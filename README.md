<p align="center">
  <img src="assets/logo.svg" alt="Dwine" width="420"/>
</p>

<h3 align="center">A Dwine desktop companion launcher plus native Fabric client mod for Minecraft 26.2.</h3>

<p align="center">
  Windows companion app · Official Minecraft Launcher handoff · Fabric 26.2 · Java 25
</p>

---

## 🎮 What Dwine is

Dwine has two pieces that work together:

- **Dwine for Windows** — a dark desktop companion app that stores its own settings locally, prepares the official Minecraft installation, installs Fabric for Minecraft 26.2, installs the bundled Dwine client mod, and opens the official Minecraft Launcher.
- **Dwine client mod** — a native Fabric 26.2 client mod bundled inside the Windows app. Press the configurable **Open Dwine** key binding (J by default) to open the in-game Dwine screen.

Dwine does **not** replace Microsoft/Mojang authentication and does not implement its own Minecraft account login. The official Minecraft Launcher remains responsible for launching the real game.

## 🖥️ Windows companion launcher

The launcher UI uses the Dwine dark dashboard design with Home, Instances, Mods, Resource Packs, Shaders and Options navigation, a quick-play card, status information, and a large Play button.

When **Play Now** is used, Dwine:

1. Detects the user's normal `.minecraft` directory.
2. Resolves a compatible Fabric loader for Minecraft 26.2.
3. Installs the Fabric profile into the normal Minecraft installation.
4. Copies the bundled `dwine-26.2.jar` into the user's `mods` directory.
5. Registers a **Dwine 26.2** installation in `launcher_profiles.json`.
6. Opens the official Minecraft Launcher.

Launcher state is stored in Dwine's own Electron user-data directory. A custom Dwine jar may still be selected for development/testing, but normal packaged builds use the bundled 26.2 jar automatically.

## 🧩 Minecraft 26.2 mod

The active 26.2 source lives in:

```text
src/main26/java/com/dwine/
```

The previous 1.21-era implementation remains under `src/main/java/com/dwine/` as migration/reference source and is intentionally excluded from the 26.2 compilation source set because Minecraft 26.2 replaced major GUI, input and rendering APIs.

The current 26.2-native layer includes:

- a Fabric client entrypoint;
- a configurable Dwine key mapping;
- a native 26.2 screen using the current GUI render-state API;
- launcher-managed Fabric 26.2 installation and local mod deployment.

Legacy 1.21 HUD/module rendering code is retained as reference rather than being falsely marked compatible with the new 26.2 rendering architecture.

## 🔨 Build the mod

Minecraft 26.2 requires Java 25 for this project.

```bash
./gradlew build
```

The mod jars are written to:

```text
build/libs/
```

## 📦 Build the Windows app

The GitHub Actions workflow builds the 26.2 mod first, embeds that exact jar in the Electron application, and then creates Windows installer and portable executables.

For local launcher development:

```bash
cd launcher
npm install
npm start
```

For Windows packaging after staging `launcher/bundled/dwine-26.2.jar`:

```bash
cd launcher
npm run dist
```

## 🧪 CI

- `Build Dwine mod` verifies the Minecraft 26.2 / Fabric / Java 25 jar.
- `Build Dwine Windows launcher` builds that mod, embeds it, then produces the Windows `.exe` artifacts.

---

<p align="center">MIT © Milkdromeda Studios</p>
