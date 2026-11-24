# Antigravity-zh-CN

<div align="center">

**🌏 [English](README_EN.md) | 简体中文**

一个为 Google Antigravity 桌面端提供完整中文界面的开源汉化补丁

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)](https://github.com/imfateone/antigravity-zh-cn)

</div>

---

## 📖 项目简介

**Antigravity 一键汉化补丁** - 为 Google Antigravity 桌面端提供完整的中文界面支持（基于 [MIMICTE/Antigravity-zh-CN](https://github.com/MIMICTE/Antigravity-zh-CN) 持续适配维护，遵循 MIT 协议）：
- 🧭 **跨平台动态探测**：自动读取 `ANTIGRAVITY_APP_DIR`、Windows 安装注册表与常见目录、macOS 应用目录（`/Applications`、`~/Applications`）定位桌面端路径，不依赖固定盘符；
- 🔄 **适配 Antigravity 2.33+/2.34+**：完整保留官方自动更新通道与扩展插件兼容性；
- 🐋 **无缝联动大肥鱼管家**：可在大肥鱼管家「反重力切号」与「工具更新」标签页一键克隆、拉取词典更新、执行汉化或还原英文。

## ✨ 核心特性

- 🚀 **零外部依赖 (Zero Dependencies)** - 自带纯原生 Python 编写的 ASAR 解包与安全校验算法，仅依赖标准库，无需安装 Node.js、npm 或 `asar` 命令行工具
- 🎯 **会话区默认零写入 & UI 槽位白名单** - 基于持久化会话宿主与硬保护边界，对用户消息、AI 裸回复/Markdown 正文、思考过程、产物预览、代码/终端、数学公式、编辑区（含 `contenteditable="plaintext-only"`）与表单提交值实行**默认零写入**；仅对已验证 UI 槽位（应用壳子、设置页、步骤状态触发器、文件汇总卡、反馈操作栏提示与时间戳、确认弹窗固定文案）做非破坏性 `Text.data` 与独立展示属性更新，绝不重写 `innerHTML` 或误翻 `2D`/`3D`/`1M` 等技术标识
- ⚡ **一键部署与热更新** - 执行补丁后自动清理桌面端进程（精准跳过 Antigravity IDE）、原子替换解包目录并重启软件，实现“双击运行 → 享受中文”的无缝体验
- 🛡️ **纯净可逆 & 失败自动回滚** - 内置跨进程文件锁、暂存目录原子切换与版本感知缓存清理；还原脚本可随时无损回滚至纯血官方英文版
- 🌐 **免 TUN 系统代理自动桥接 & 启动器保护** - 原生通过 Electron `resolveProxy` 读取系统代理与 PAC（支持任意端口与 Clash / v2rayN / Surge 等代理软件），安全透传给语言服务 `language_server`（可通过 `ANTIGRAVITY_DISABLE_SYSTEM_PROXY_BRIDGE=1` 关闭），同时自动识别并保留桌面自定义代理快捷方式（如 `pythonw.exe` 包装器）
- 🧭 **全动态跨平台支持** - 原生支持 Windows 及 macOS（Intel 与 Apple Silicon）环境下的路径寻址与进程管理

## 📦 安装与使用

### 方式一：从源码一键运行 ⭐ 推荐

**1. 克隆仓库**
```bash
git clone https://github.com/imfateone/antigravity-zh-cn.git
cd antigravity-zh-cn
```

**2. 执行汉化或还原**

- **Windows 双击一键运行**：
  - 汉化：双击运行 [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat)（自动依次检测 `python`、`py -3` 或 `uv`）
  - 还原：双击运行 [`一键还原官方英文.bat`](一键还原官方英文.bat)
- **命令行运行（Windows / macOS）**：
  ```bash
  # 执行汉化
  python Antigravity-Patcher.py
  # 或使用 uv
  uv run --no-project python Antigravity-Patcher.py

  # 还原官方英文版
  python Restore.py
  ```
- **可选参数与环境变量**：
  - `--no-relaunch`：注入或还原完成后不自动重启客户端
  - `--no-pause`：执行结束后不等待回车（适合脚本或外部管理器静默调用）
  - `ANTIGRAVITY_APP_DIR`：手动指定自定义 Antigravity 安装目录
  - `ANTIGRAVITY_DISABLE_SYSTEM_PROXY_BRIDGE=1`：禁用系统代理自动桥接（回退为完全不读取系统代理的默认行为）

---

### 方式二：独立免安装版 (Windows / macOS)

如果目标机器未安装 Python，可前往 [Releases](../../releases) 下载对应系统的预编译可执行包，或参考下方「维护与打包」章节自行构建单文件可执行程序。

- **Windows**：解压后双击运行 `Antigravity-Patcher.exe` 开始汉化（还原运行 `Restore.exe`）
- **macOS**（`arm64` 为 M 系列芯片，`x86_64` 为 Intel 芯片）：
  ```bash
  chmod +x Antigravity-Patcher-macOS-*
  ./Antigravity-Patcher-macOS-*
  ```
  > 🍎 **Mac 用户注意**：若系统提示“无法打开，因为无法验证开发者”，请前往「系统设置 -> 隐私与安全性」点击「仍要打开」，或在终端执行 `xattr -cr Antigravity-Patcher-macOS-*` 解除隔离属性。

## 💡 技术原理

本项目利用 Electron 框架机制实现非破坏性界面汉化：

### 1. 免打包劫持 (Unpacked Patching)
在暂存目录解包并完成注入后再原子切换为 `resources/app`，随后将官方 `app.asar` 重命名为 `app.asar.disabled`，使 Electron 直接加载汉化后的解包目录；若途中发生任何异常则自动清理暂存目录并保留原状态。

### 2. 会话区默认零写入与分帧调度

渲染器先确认节点属于已知 UI 槽位，再翻译单个 `Text.data` 或独立展示属性（`placeholder`、`title`、`aria-label`、`data-tooltip`、`data-title`）。会话正文、思考面板、产物预览、编辑区和表单业务值保留原文。思考 Portal 按元素身份与变更顺序日志保护：即便触发按钮在首次扫描前卸载、同批次连续改绑，或原面板移除/修改 ID、被同 ID 节点遮挡，正在显示的内容与属性仍保持零写入；触发器与原面板均卸载后，复用同 ID 的普通界面节点可正常汉化。

全局观察器仅监听结构与有限展示属性，不开启全树 `characterData` 监听；文本观察器仅按需绑定至已授权动态 UI 节点，局部属性观察器负责保留节点脱离后应用自身的赋值。初次扫描、脱离子树清理、Portal 归属结算和翻译写入共享每帧 4 ms 目标预算。无头 Chromium 基准下，原位流式正文触发 0 条翻译观察记录，结构化正文插入触发 0 次子树查询。

### 3. 原生 ASAR 解析器与更新守护
使用纯 Python 标准库实现 ASAR 解析器，内置路径穿越拦截、偏移越界检查与跨进程文件锁（防止汉化与还原并发冲突）；同时自动按语义化版本号比对清理过期的已安装更新包缓存，保留更高版本的待装更新包。

### 4. 自动化测试
```bash
uv run --no-project python -m unittest discover -s tests -v
# 或
python -m unittest discover -s tests -v
```
共包含 15 项测试套件，涵盖 ASAR 解包安全校验、补丁热更新与失败回滚、更新缓存版本守护、跨进程锁、自定义代理快捷方式保留、系统代理桥接（PAC 解析、WSL/显式代理跳过、超时 Fail-Open）、词典重复键与静态安全不变量检查、Node 纯文案格式化回归，以及基于真实无头 Chromium 的全量回归（正文零写入、Portal 历史归属与同 ID 复用、跨帧裁剪游标恢复、脱离子树跨微任务赋值保留、2,000 轮对话与 2,000 文本块流式零开销、2,000 个按钮冷启动与重挂载零闪回/无长任务）。需安装 Node.js 22+ 与 Chromium 内核浏览器（Chrome 或 Edge）以运行浏览器用例。

### 5. 维护与打包

- [Antigravity-Patcher.py](Antigravity-Patcher.py) 负责安装、版本切换和注入；[Restore.py](Restore.py) 负责无损还原；[_ag_common.py](_ag_common.py) 提供跨平台寻址、进程控制、文件锁、自定义启动器快捷方式识别与更新缓存管理。
- [catalog.js](antigravity_localization/renderer/catalog.js) 保存词典；[formatters.js](antigravity_localization/renderer/formatters.js) 处理时长、状态和动态文案模式。
- [antigravity_dom.js](antigravity_localization/renderer/antigravity_dom.js) 定义 Antigravity DOM 槽位与正文硬保护边界；[engine.js](antigravity_localization/renderer/engine.js) 负责分帧调度、属性/文本写入和节点生命周期。
- [mount_walk.js](antigravity_localization/renderer/mount_walk.js) 在节点或祖先被跨帧移除时保持后续扫描不中断；[portal_registry.js](antigravity_localization/renderer/portal_registry.js) 按元素身份和变更顺序日志管理思考面板保护。
- [menu.js](antigravity_localization/renderer/menu.js) 负责 Electron 原生顶部菜单栏汉化；[system_proxy.js](antigravity_localization/renderer/system_proxy.js) 负责按需将系统代理透传给 `language_server`。
- [Antigravity-Patcher.spec](Antigravity-Patcher.spec) 将渲染器资源并入单文件发行包，可在仓库根目录执行 `uvx pyinstaller Antigravity-Patcher.spec` 构建。

## ⚠️ 已知限制

- **对话正文与思考内容保持原文** - 为严格保障“正文零写入”、避免篡改代码/技术词与用户数据，用户发送的消息、AI 回复正文、思考过程日志及产物预览正文均按设计保持原文，仅汉化前端 UI 界面壳子与已验证控件槽位
- **多平台支持** - 已支持 Windows 及 macOS（Intel 与 Apple Silicon），Linux 暂未适配
- **版本依赖** - 当前 DOM 槽位适配面向 Antigravity 2.34；客户端升级后，新增或结构变更的未识别 UI 槽位将安全回退并保留英文原文

## 📸 效果展示

<div align="center">

![antigravity-chinese](antigravity-chinese.png)

*Antigravity 界面汉化示例*

</div>

**界面汉化范围示例**
- ✅ 侧边栏导航（新建对话、自动化/计划任务、插件市场、项目列表与相对时间）
- ✅ 顶部菜单栏与系统托盘（文件、编辑、视图、窗口、帮助及托盘状态菜单）
- ✅ 对话输入框占位提示文本、底部操作栏与模型选择器
- ✅ 已适配的设置页面分类、选项标题和详细说明
- ✅ 会话内步骤状态折叠条、文件修改汇总卡、终端/文件权限确认卡片及撤销/重做弹窗

> 💡 提示：双击运行 [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat) 或执行 `python Antigravity-Patcher.py` 即可体验完整的中文界面！

## 🔐 安全性说明

本项目完全开源透明：

### ✅ 我们做了什么

- **仅修改本地前端展示文案与可选语言服务代理继承** - 只在本地客户端替换界面显示文本，并在语言服务启动瞬间按需把当前系统的 HTTP/PAC 代理临时透传给子进程，不拦截或上传任何数据、不接触账号凭证
- **不污染会话与模型上下文** - 不修改本地历史对话记录文件，也不干预后台语言服务发往模型接口的 Prompt 与工具调用负载
- **开源可审计 & 完全可逆** - 纯 Python 与原生 JavaScript 明文源码，无混淆或联网逻辑，随时可通过还原脚本一键恢复官方原版

### 🛡️ 本地文件变更范围

1. **`resources/app`（解包目录）** - 向 `dist/preload.js`、`dist/menu.js` 与 `dist/languageServer.js` 注入本地化与系统代理桥接脚本（带唯一标记，支持幂等热更新），并替换 `dist/tray.js`、`dist/main.js`、`dist/provisionSplash.js`、`dist/loadingOverlay.js` 中的托盘、退出确认框与启动页固定文案
2. **`resources/app.asar.disabled`** - 原封不动保留官方原始 `app.asar` 备份，供还原或版本校验使用

### 关于免安装可执行版 (Windows .exe / macOS 二进制文件)

- 使用开源工具 [PyInstaller](https://pyinstaller.org/) 打包，内含 Python 运行时（体积约 8 MB）
- Windows 下可能触发部分杀毒软件对 PyInstaller 引导程序的通用误报
- macOS 下因未使用付费开发者证书签名，首次运行可能提示“无法验证开发者”
- 如有安全顾虑，推荐直接使用“从源码运行”方式（代码完全透明）

## ❓ 常见问题

<details>
<summary><b>Q: 汉化会篡改会话记录，或者影响大模型的缓存命中（Prompt Cache）吗？</b></summary>

A: **完全不会。**
1. 本补丁仅作用于 Electron 前端窗口的 DOM 展示层，会话区消息正文、思考过程日志、代码块、输入框业务提交值与磁盘上的会话记录均为零写入。
2. 大模型的前缀缓存命中取决于后台语言服务进程发往服务端的 System Prompt、工具定义与历史消息数组，本补丁不触碰后台语言服务或任何网络请求，缓存命中计算与原版 100% 一致。
</details>

<details>
<summary><b>Q: Antigravity 官方更新客户端后，这个汉化补丁还能继续使用吗？</b></summary>

A: **可以。**
客户端更新后会写入新版官方 `app.asar`，界面暂时恢复英文。重新运行一次汉化补丁即可：脚本会自动检测官方核心包变更，在暂存目录重新解包、注入并原子切换。若新版客户端调整了部分组件的 DOM 结构，未识别槽位会安全保留英文原文，在 DOM 适配层补充对应槽位即可。
</details>

<details>
<summary><b>Q: 如何添加或修改翻译词条？</b></summary>

A: 在 [catalog.js](antigravity_localization/renderer/catalog.js) 的 `dictionary` 中添加或修改键值对：
```javascript
"English Text": "中文翻译",
```
保存后重新执行 `python Antigravity-Patcher.py`（或双击 `一键汉化Antigravity.bat`）即可热更新生效。
</details>

<details>
<summary><b>Q: Mac 版本运行提示“无法打开，因为无法验证开发者”怎么办？</b></summary>

A: 这是 macOS Gatekeeper 对未签名开源程序的默认限制。解决方法：
1. 方式一：前往「系统设置」 -> 「隐私与安全性」，向下滑动并点击「仍要打开」。
2. 方式二：在终端执行 `xattr -cr 你下载的程序路径` 解除隔离属性。
</details>

<details>
<summary><b>Q: Python 脚本版和免安装可执行版有什么区别？</b></summary>

A:
- **Python 源码版**：文件极小、代码完全透明、无杀软误报，支持直接修改词典热更新（需本地安装 Python 3.8+ 或 `uv`）。
- **免安装可执行版**：内置 Python 运行时（约 8 MB），无需配置环境、开箱即用，但可能被部分杀软误报。

两者汉化逻辑与效果完全一致。
</details>

<details>
<summary><b>Q: 为什么执行命令时提示 "Python 不是内部或外部命令"？</b></summary>

A: 说明 `python` 未加入系统 `PATH`。Windows 用户可直接双击仓库根目录的 [`一键汉化Antigravity.bat`](一键汉化Antigravity.bat)（会自动尝试 `py -3` 和 `uv`），或重新安装 Python 并勾选 `Add Python to PATH`。
</details>

<details>
<summary><b>Q: 为什么有时 Antigravity 打开没有界面？是脚本损坏了软件吗？</b></summary>

A: 通常不是软件损坏，而是 Electron 后台进程或杀软拦截导致，可按以下步骤排查：
1. 检查右下角**系统托盘**，双击 Antigravity 图标唤醒窗口。
2. 打开任务管理器（`Ctrl+Shift+Esc`），结束残留的 `Antigravity.exe` 进程后重新启动。
3. 若被杀毒软件隔离了解包目录中的文件，运行 [`一键还原官方英文.bat`](一键还原官方英文.bat) 或 `python Restore.py`（独立版运行 `Restore.exe`）恢复官方原版，将目录加入杀软白名单后再重新汉化。
</details>

<details>
<summary><b>Q: 支持哪些操作系统？</b></summary>

A: 支持 **Windows** 与 **macOS**（Intel 及 Apple Silicon 芯片）。Linux 版本暂未适配。
</details>

更多问题？欢迎在 [GitHub Issues](../../issues) 或 [Discussions](../../discussions) 中交流！

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

- 发现翻译错误或遗漏？请提交 [Issue](../../issues) 或直接 PR 修改
- 有更好的技术方案？欢迎在 [Discussions](../../discussions) 讨论

详细的贡献指南请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## ⚠️ 免责声明

- 本项目仅供学习交流使用
- 使用本补丁造成的任何问题由用户自行承担
- 请使用正版 Antigravity 软件并遵守其服务条款

## 🌟 Star History

如果这个项目对你有帮助，欢迎点亮一颗 Star ⭐️！

## 📧 联系方式

- Issues: [GitHub Issues](../../issues)
- Discussions: [GitHub Discussions](../../discussions)

---

<div align="center">

**Made with ❤️ by Antigravity-zh-CN Contributors**

</div>
