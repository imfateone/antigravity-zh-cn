# Antigravity-zh-CN

<div align="center">

**🌏 English | [简体中文](README.md)**

An open-source Chinese localization patch for Google Antigravity Desktop

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)](https://github.com/imfateone/antigravity-zh-cn)

</div>

---

## 📖 Project Overview

**Antigravity Chinese Localization Patch** - Provides complete Chinese interface support for Google Antigravity Desktop (maintained on top of [MIMICTE/Antigravity-zh-CN](https://github.com/MIMICTE/Antigravity-zh-CN) under the MIT License):
- 🧭 **Cross-Platform Path Discovery**: Automatically locates Antigravity via `ANTIGRAVITY_APP_DIR`, Windows Registry & common install paths, and macOS `/Applications` & `~/Applications`;
- 🔄 **Antigravity 2.33+/2.34+ Ready**: Preserves the official auto-update channel and extension/plugin compatibility.

## ✨ Key Features

- 🚀 **Zero External Dependencies** - Built-in pure-Python ASAR extractor with integrity and path-traversal checks using only the standard library—no Node.js, npm, or `asar` CLI required
- 🎯 **Chat-Zone Default Zero-Write & UI Slot Whitelist** - Enforces default zero writes across user messages, bare/Markdown assistant replies, expanded thinking panels, artifact previews, code/terminal/math blocks, editable regions (including `contenteditable="plaintext-only"`), and form submission values; only verified UI slots (app shell, Settings, step triggers, file summary cards, feedback toolbar tooltips & timestamps, confirmation dialog chrome) are updated via non-destructive `Text.data` and independent display attributes—zero `innerHTML` rewrites and no false positives on `2D`/`3D`/`1M`
- ⚡ **One-Click Deployment & Hot Update** - Automatically stops desktop processes (safely skipping Antigravity IDE), atomically swaps the unpacked bundle, and relaunches the app
- 🛡️ **Clean, Reversible & Crash-Safe** - Includes cross-process file locking, staging-directory atomic swap with automatic rollback, and version-aware updater cache cleanup; `Restore.py` rolls back cleanly to the official English build at any time
- 🧭 **Cross-Platform Support** - Natively supports path resolution and process management on Windows and macOS (Intel & Apple Silicon)

## 📦 Installation & Usage

### Option 1: Run from Source ⭐ Recommended

**1. Clone the repository**
```bash
git clone https://github.com/imfateone/antigravity-zh-cn.git
cd antigravity-zh-cn
```

**2. Apply or restore**

- **Windows one-click batch scripts**:
  - Apply patch: double-click [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat) (automatically detects `python`, `py -3`, or `uv`)
  - Restore English: double-click [`一键还原官方英文.bat`](一键还原官方英文.bat)
- **Command line (Windows / macOS)**:
  ```bash
  # Apply Chinese localization
  python Antigravity-Patcher.py
  # or via uv
  uv run --no-project python Antigravity-Patcher.py

  # Restore official English client
  python Restore.py
  ```
- **Optional flags & environment variables**:
  - `--no-relaunch`: Skip automatic app relaunch after patching/restoring
  - `--no-pause`: Exit immediately without waiting for Enter (useful for automation)
  - `ANTIGRAVITY_APP_DIR`: Explicitly specify a custom Antigravity installation directory

---

### Option 2: Standalone Executables (Windows / macOS)

If Python is not installed on the target machine, download a prebuilt archive from [Releases](../../releases), or build a single-file binary yourself (see "Maintenance and Packaging" below).

- **Windows**: Extract and run `Antigravity-Patcher.exe` (run `Restore.exe` to revert)
- **macOS** (`arm64` for Apple Silicon, `x86_64` for Intel):
  ```bash
  chmod +x Antigravity-Patcher-macOS-*
  ./Antigravity-Patcher-macOS-*
  ```
  > 🍎 **macOS Note**: If Gatekeeper reports "cannot be opened because the developer cannot be verified", allow it under "System Settings -> Privacy & Security -> Open Anyway" or run `xattr -cr Antigravity-Patcher-macOS-*` in Terminal.

## 💡 Technical Approach

This project localizes the Electron client non-destructively:

### 1. Atomic Unpacked Patching
Extracts and patches `app.asar` inside a temporary staging directory before atomically swapping it into `resources/app` and renaming `app.asar` to `app.asar.disabled`. Any failure during extraction or injection rolls back cleanly without corrupting the existing installation.

### 2. Chat Content Is Read-Only by Default

The renderer verifies that a node belongs to a recognized UI slot before translating its `Text.data` or an independent display attribute (`placeholder`, `title`, `aria-label`, `data-tooltip`, `data-title`). Messages, thinking panels, artifact previews, editors, and form values retain their original content. Thinking portals are protected by element identity and a versioned mutation journal: even if a trigger unmounts before initial discovery, retargets multiple times in one batch, or a mounted panel drops/renames its ID or is shadowed by an earlier duplicate ID, the active panel remains zero-write; once both trigger and panel unmount, ordinary UI elements recycling that ID localize normally.

The global observer watches structure and a bounded attribute filter without whole-tree `characterData` observation. Text observers attach only to authorized dynamic UI nodes, and local attribute observers preserve application writes made while a node is detached. Initial discovery, bulk cleanup, portal ownership settlement, and display writes share a 4 ms per-frame target budget. In headless Chromium benchmarks, in-place prose streaming generates zero localization observer records, and structured prose inserts execute zero subtree queries.

### 3. Native ASAR Parser & Updater Guard
Pure-Python standard-library ASAR extractor with path-traversal validation, bounds checks, cross-process locking between patch and restore, and semver-aware cleanup of already-installed updater cache installers (preserving newer pending updates).

### 4. Automated Tests
```bash
uv run --no-project python -m unittest discover -s tests -v
# or
python -m unittest discover -s tests -v
```
Runs 13 test suites covering ASAR extraction security, hot-update & failure rollback, updater cache version guards, cross-process locking, dictionary duplicate-key & static DOM safety invariants, Node text formatters, and headless Chromium regressions (zero content writes, journaled portal lifecycle & ID reuse, cross-frame cursor recovery, post-detach cross-microtask assignments, 2,000-turn & 2,000-span streaming benchmarks, and 2,000-button cold start & remount without flashbacks or long tasks). Node.js 22+ and a Chromium-based browser (Chrome or Edge) are required for the browser suites.

### 5. Maintenance and Packaging

- [Antigravity-Patcher.py](Antigravity-Patcher.py) handles installation, version transitions, and injection; [Restore.py](Restore.py) handles lossless rollback; [_ag_common.py](_ag_common.py) provides cross-platform path resolution, process control, locking, and updater cache management.
- [catalog.js](antigravity_localization/renderer/catalog.js) stores the dictionary; [formatters.js](antigravity_localization/renderer/formatters.js) formats durations, statuses, and dynamic UI labels.
- [antigravity_dom.js](antigravity_localization/renderer/antigravity_dom.js) defines Antigravity's UI slots and hard content-protection boundaries; [engine.js](antigravity_localization/renderer/engine.js) handles frame scheduling, writes, and node lifecycles.
- [mount_walk.js](antigravity_localization/renderer/mount_walk.js) resumes discovery across frames when nodes or ancestors are removed; [portal_registry.js](antigravity_localization/renderer/portal_registry.js) tracks thinking panels by element identity and mutation history.
- [menu.js](antigravity_localization/renderer/menu.js) localizes the native Electron application menu.
- [Antigravity-Patcher.spec](Antigravity-Patcher.spec) bundles the renderer modules into a standalone executable via `uvx pyinstaller Antigravity-Patcher.spec`.

## ⚠️ Known Limitations

- **Chat Prose & Thinking Logs Preserved Verbatim** - By design, user messages, assistant reply prose, expanded thinking logs, and artifact preview content are strictly zero-write to prevent tampering with code, technical tokens, or user data; only frontend UI chrome and verified control slots are localized
- **Platform Support** - Supports Windows and macOS (Intel & Apple Silicon). Linux is not currently supported
- **Version Specific** - The current DOM slot adapter targets Antigravity 2.34; unrecognized slots after a future client update safely retain their original English text until adapted

## 📸 Screenshots

<div align="center">

![Antigravity Chinese Interface](antigravity-chinese.png)

*Example of the localized Antigravity interface*

</div>

**Examples of localized UI**
- ✅ Sidebar navigation (New conversation, Automations, Plugins, project list & relative timestamps)
- ✅ Top menu bar & system tray (File, Edit, View, Window, Help, and tray status menu)
- ✅ Composer placeholder, footer controls, and model selector
- ✅ Supported categories, options, and descriptions in Settings
- ✅ Step collapsible triggers, changed-files summary cards, inline permission prompts, and undo/redo confirmation dialogs

> 💡 Tip: Double-click [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat) or run `python Antigravity-Patcher.py` to experience the localized interface!

## 🔐 Security

This project is completely open-source and auditable:

### ✅ What We Do

- **Local UI Display Only** - Replaces frontend UI display strings locally without intercepting network traffic, collecting telemetry, or accessing account credentials
- **Zero Impact on Transcripts or Model Context** - Never modifies local conversation history files or the prompts, tool schemas, and messages sent by the background language server to model APIs
- **Open Source & Reversible** - Plain Python and JavaScript source with zero obfuscation and one-click lossless rollback

### 🛡️ Local File Footprint

1. **`resources/app` (unpacked bundle)** - Appends idempotent marker-guarded blocks to `dist/preload.js` and `dist/menu.js`, and localizes static tray/quit/splash strings in `dist/tray.js`, `dist/main.js`, `dist/provisionSplash.js`, and `dist/loadingOverlay.js`
2. **`resources/app.asar.disabled`** - Preserves the unmodified official `app.asar` archive for instant restoration and version checks

### About Standalone Executables

- Built with [PyInstaller](https://pyinstaller.org/) (~8 MB including the embedded Python runtime)
- May trigger generic PyInstaller bootloader false positives in some Windows antivirus scanners
- Unsigned on macOS, which triggers the standard Gatekeeper prompt on first run
- Running from source is recommended if you prefer zero binary packaging

## ❓ FAQ

<details>
<summary><b>Q: Does this patch alter conversation history or affect model Prompt Cache hits?</b></summary>

A: **No.**
1. Localization operates strictly on authorized DOM UI slots in the Electron renderer; chat messages, thinking logs, code blocks, editor values, and on-disk transcript files receive zero writes.
2. Prompt caching depends on the system prompt, tool definitions, and message history sent by the background language server to the model API—none of which pass through the frontend DOM or are touched by this patch.
</details>

<details>
<summary><b>Q: Can I continue using this patch after an official Antigravity update?</b></summary>

A: **Yes.**
When the client updates, it writes a new `app.asar` and temporarily reverts to English. Simply rerun the patcher—it detects the new official bundle, extracts and injects in a staging directory, and atomically switches over. Any newly introduced UI slots that are not yet recognized safely remain in English.
</details>

<details>
<summary><b>Q: How do I add or edit translations?</b></summary>

A: Add or update key-value pairs in the `dictionary` inside [catalog.js](antigravity_localization/renderer/catalog.js):
```javascript
"English Text": "中文翻译",
```
Then rerun `python Antigravity-Patcher.py` (or `一键汉化Antigravity.bat`) to hot-update the unpacked bundle.
</details>

<details>
<summary><b>Q: macOS reports "cannot be opened because the developer cannot be verified"?</b></summary>

A: This is macOS Gatekeeper's default prompt for unsigned open-source binaries:
1. Go to "System Settings -> Privacy & Security", scroll down, and click "Open Anyway"; or
2. Run `xattr -cr /path/to/binary` in Terminal.
</details>

<details>
<summary><b>Q: What is the difference between the source script and standalone executable?</b></summary>

A:
- **Source script**: Tiny footprint, fully transparent source, no antivirus false positives, easy dictionary editing (requires Python 3.8+ or `uv`).
- **Standalone executable**: Bundles the Python runtime (~8 MB) so no Python setup is required, though some antivirus tools flag PyInstaller binaries.

Both share the exact same localization engine.
</details>

<details>
<summary><b>Q: "Python is not recognized as an internal or external command"?</b></summary>

A: Python is not on your `PATH`. On Windows, try double-clicking [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat) (which also checks `py -3` and `uv`), or reinstall Python with `Add Python to PATH` checked.
</details>

<details>
<summary><b>Q: Why does Antigravity sometimes open without a visible window?</b></summary>

A: Usually this is caused by a background Electron instance or antivirus quarantine rather than bundle corruption:
1. Check the **System Tray** and double-click the Antigravity icon.
2. Open Task Manager (`Ctrl+Shift+Esc`), terminate any lingering `Antigravity.exe` processes, and relaunch.
3. If an antivirus quarantined unpacked files, run [`一键还原官方英文.bat`](一键还原官方英文.bat) or `python Restore.py` (`Restore.exe` for standalone), whitelist the folder, and apply the patch again.
</details>

<details>
<summary><b>Q: Which operating systems are supported?</b></summary>

A: **Windows** and **macOS** (both Intel and Apple Silicon). Linux is not currently supported.
</details>

More questions? Feel free to open an issue in [GitHub Issues](../../issues) or [Discussions](../../discussions)!

## 🤝 Contributing

Issues and Pull Requests are welcome!

- Found translation errors or omissions? Submit an [Issue](../../issues) or PR
- Have technical suggestions? Join [Discussions](../../discussions)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## ⚠️ Disclaimer

- Provided for educational and personal localization purposes only
- Use at your own discretion with official Google Antigravity builds and in compliance with its Terms of Service

## 🌟 Star History

If this project helps you, please consider giving it a Star ⭐️!

## 📧 Contact

- Issues: [GitHub Issues](../../issues)
- Discussions: [GitHub Discussions](../../discussions)

---

<div align="center">

**Made with ❤️ by Antigravity-zh-CN Contributors**

</div>
