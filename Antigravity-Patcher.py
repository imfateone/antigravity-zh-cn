# coding: utf-8
import glob
import os
import json
import struct
import subprocess
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _ag_common import (  # noqa: E402
    cleanup_stale_updater_cache,
    find_app_dir,
    get_desktop_dir,
    get_resources_dir,
    is_antigravity_running,
    relaunch_antigravity,
    stop_antigravity_desktop_processes,
)

_resolve_resources_dir = get_resources_dir


APP_DIR = find_app_dir()
RESOURCES_DIR = _resolve_resources_dir(APP_DIR)
ASAR_PATH = os.path.join(RESOURCES_DIR, "app.asar") if RESOURCES_DIR else ""
UNPACKED_APP_DIR = os.path.join(RESOURCES_DIR, "app") if RESOURCES_DIR else ""

DOM_TRANSLATOR_INJECTION = r"""
// Antigravity Chinese Localization Engine
(function() {
  const dictionary = {
    // === v2.30.0 Full Source-Verified UI Dictionary ===
    "Updater": "更新管理",
    "Accessibility": "无障碍",
    "Screen Reader Mode": "屏幕阅读器模式",
    "Optimize the interface and terminal output for screen readers.": "针对屏幕阅读器优化界面与终端输出。",
    "Chat Input": "对话输入",
    "Chat Layout": "对话布局",
    "Interface Layout": "界面布局",
    "Conversation Steps": "对话步骤详情",
    "Choose how much detail is shown during a conversation.": "选择对话过程中展示的执行细节详略程度。",
    "Verbose": "详细",
    "Context and Quota Indicator": "上下文与配额指示器",
    "Context usage": "上下文用量",
    "Show how full the context window is next to the send button. Click it for a breakdown and to see your model quota.": "在发送按钮旁显示上下文窗口占用比例，点击可查看明细与模型配额。",
    "Markdown Artifact Width": "Markdown 产物宽度",
    "Configure the default width of markdown artifacts.": "配置 Markdown 产物文档的默认显示宽度。",
    "Markdown view mode": "Markdown 视图模式",
    "Fit Mode": "自适应模式",
    "Fill": "铺满",
    "Terminal Placement": "终端位置",
    "Choose where terminal sessions appear.": "选择终端会话的默认显示位置。",
    "Bottom Panel": "底部面板",
    "Side Panel": "侧边面板",
    "Custom Context Menus": "自定义右键菜单",
    "Replace the default browser right-click menu with quick actions.": "使用快捷操作菜单替换默认的浏览器右键菜单。",
    "Enter to Send": "按 Enter 发送",
    "Send messages with the keyboard's Enter key instead of starting a new line.": "使用键盘 Enter 键直接发送消息，而不是换行。",
    "Interrupt the agent and send immediately.": "打断智能体当前操作并立即发送。",
    "Queue until after the current turn.": "排队等待当前轮次结束后发送。",
    "Sends after agent finishes working": "在智能体完成当前工作后发送",
    "Command Setup Script": "命令前置初始化脚本",
    "A shell setup script run before every command the agent executes.": "在智能体执行每条终端命令前自动运行的 Shell 初始化脚本。",
    "Enable Sandbox Mode": "启用沙盒模式",
    "Sandbox Allow Network": "允许沙盒联网",
    "Allow sandboxed commands to make network requests.": "允许在沙盒中运行的命令发起网络请求。",
    "Run terminal commands with sandbox restrictions.": "在沙盒安全限制下运行终端命令。",
    "Restricts agent tools to a secure, isolated local sandbox.": "将智能体工具限制在安全隔离的本地沙盒环境中。",
    "Terminal Command Auto Execution": "终端命令自动执行策略",
    "Proceed in Sandbox": "沙盒内自动放行",
    "Terminal command automatically proceeds if the command runs inside the sandbox. Otherwise, it requests review.": "若终端命令在沙盒内运行则自动放行，否则请求人工审阅。",
    "The agent always asks for confirmation before executing terminal commands (except those in the Allow list).": "智能体在执行终端命令前始终请求确认（白名单中的命令除外）。",
    "The agent always asks for review.": "智能体始终请求人工审阅。",
    "Agent always asks for review.": "智能体始终请求人工审阅。",
    "Every command requires approval.": "每条命令均需批准。",
    "Automatically decide if commands run.": "自动判断命令是否可直接运行。",
    "Run all commands without restrictions.": "无限制自动运行所有命令。",
    "Controls whether terminal commands require your approval before running.": "控制终端命令在运行前是否需要您的批准。",
    "Agent Non-Workspace File Access": "工作区外文件访问权限",
    "Outside of folders file access policy": "工作区目录外文件访问策略",
    "Configures how the agent tries to access files outside of its working folders.": "配置智能体访问工作目录以外文件时的权限策略。",
    "Review Policy": "审阅策略",
    "Specifies the agent's behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience.": "指定智能体在创建产物文档时向您请求审阅的方式。",
    "Default Customizations": "默认定制项",
    "Include Jetski Default Customizations": "包含内置默认定制项",
    "Include default customizations, such as default skills.": "包含系统内置的默认定制项（如内置技能）。",
    "When enabled, the agent will include default customizations, including default skills.": "启用后，智能体将自动加载内置默认定制项（包括默认技能）。",
    "Customize Global Skills": "管理全局技能",
    "Configure built-in browser, link opening, and browser subagent preferences.": "配置内置浏览器、链接打开方式及浏览器子智能体偏好。",
    "Configure allowed and denied URLs for the browser subagent. It runs in the built-in browser, so no separate browser install is needed.": "配置浏览器子智能体允许与禁止访问的网址列表。它在内置浏览器中运行，无需额外安装浏览器。",
    "Choose where links open by default when clicked.": "选择点击链接时的默认打开方式。",
    "Enable Browser Tools": "启用浏览器工具",
    "Folder where files downloaded in the built-in browser are saved.": "内置浏览器下载文件的默认保存文件夹。",
    "Download Location": "下载保存位置",
    "Default Workspace VCS": "默认工作区版本控制 (VCS)",
    "VCS used when creating a new workspace, including workspaces generated based off your initial prompt.": "创建新工作区（包括根据初始提示词自动生成的工作区）时使用的版本控制系统。",
    "Sync JJ Worktrees to Head": "同步 JJ 工作树至最新提交",
    "Sync newly created JJ worktrees to head when starting a conversation.": "开启对话时将新建的 JJ 工作树同步至最新提交。",
    "Configure global allowed and denied resource permissions.": "配置全局允许与拒绝的资源访问权限。",
    "Configure workspace-specific permissions, resources, and customizations.": "配置当前工作区专属的权限、资源与定制项。",
    "Configure GitHub access policies.": "配置 GitHub 访问权限策略。",
    "Manage fine-grained permissions for GitHub.": "管理 GitHub 细粒度访问权限。",
    "GitHub Permissions": "GitHub 权限",
    "GitHub Policies": "GitHub 策略",
    "GitHub Personal Access Token": "GitHub 个人访问令牌",
    "Cloud Permissions": "云端权限",
    "Permission Settings": "权限设置",
    "Permission Details": "权限详情",
    "Nickname": "设备昵称",
    "A nickname for identifying this application in the companion website. Changing this will restart the connection.": "用于在配套网页端识别此客户端的昵称，修改后将重新建立连接。",
    "A label for this computer when you connect from another device. Changing it reconnects.": "从其他设备连接时显示的本机名称标签，修改后将重新连接。",
    "Manage your conversations from the companion website.": "从配套网页端管理您的对话。",
    "Continue your work from another device with Remote Control. Scan the QR code or open the link below.": "通过远程控制在另一台设备上继续工作。请扫描二维码或打开下方链接。",
    "Get started with Remote Control": "开始使用远程控制",
    "Show Remote Control QR code": "显示远程控制二维码",
    "Remote Control Instances": "远程控制实例",
    "Background tasks and terminals agents left running, across all conversations.": "所有对话中智能体仍在后台运行的任务与终端。",
    "Nothing is running right now": "当前没有正在运行的任务",
    "Enable Notifications": "启用通知",
    "Chime volume": "提示音音量",
    "Accounts": "账户",
    "Signed-in accounts": "已登录账户",
    "Not Signed In": "未登录",
    "Signing Out...": "正在退出登录...",
    "Sign in again": "重新登录",
    "Sign in with a different account": "使用其他账户登录",
    "Continue with Google": "通过 Google 继续",
    "Continue with Google Cloud": "通过 Google Cloud 继续",
    "Your Plan": "您的订阅方案",
    "Billing model": "计费模式",
    "Select Billing Model": "选择计费模式",
    "Subscription": "订阅方案",
    "Pay As You Go": "按量计费",
    "Pay only for the tokens you use, billed through Gemini platform.": "仅按实际消耗的 Token 付费，通过 Gemini 平台结算。",
    "Use Antigravity through your Gemini subscription.": "通过您的 Gemini 订阅方案使用 Antigravity。",
    "Purchase Credits": "购买积分",
    "Enable Overages": "启用超额计费",
    "Insufficient AI Credits": "AI 积分不足",
    "Quota": "配额",
    "Usage": "使用量",
    "Refresh quota and credits data": "刷新配额与积分数据",
    "No quota information available.": "暂无配额信息。",
    "Baseline model quota reached": "已达基础模型配额上限",
    "Model quota reached": "已达模型配额上限",
    "Daily conversation limit reached": "已达每日对话次数上限",
    "Conversation limit reached": "已达对话长度上限",
    "Invite a Friend": "邀请好友",
    "Google One Referral": "Google One 推荐计划",
    "Share your referral link with friends": "与好友分享您的推荐链接",
    "Manage License": "管理许可证",
    "Select License": "选择许可证",
    "Select your license": "选择您的许可证",
    "Available licenses": "可用许可证",
    "Choose Region": "选择区域",
    "United States": "美国",
    "Europe": "欧洲",
    "Delete All Data": "删除所有数据",
    "Delete All Remote Agents Data": "删除所有远程智能体数据",
    "Delete All Remote Agents Data?": "确定删除所有远程智能体数据吗？",
    "Manage and delete your data anytime": "随时管理与删除您的数据",
    "Explore the plugin marketplace": "浏览插件市场",
    "Explore other marketplace customizations": "探索市场中的其他定制扩展",
    "Find plugins - bundles of skills, agents, MCP servers, UI extensions and more, and install them in one click.": "查找并一键安装插件（包含技能、智能体、MCP 服务器、界面扩展等组合包）。",
    "Curated sets of plugins for common workflows and roles.": "面向常见工作流与角色精选的插件套装。",
    "Each plugin can be managed on its own.": "每个插件均可独立管理。",
    "Bundles": "插件套装",
    "What's in this bundle": "套装包含内容",
    "This bundle has no plugins yet.": "此套装暂无插件。",
    "Currently installed": "当前已安装",
    "Create plugin": "创建插件",
    "Delete plugin": "删除插件",
    "Plugin details": "插件详情",
    "Plugin metadata": "插件元数据",
    "Plugin update required": "插件需要更新",
    "Loading plugins...": "正在加载插件...",
    "Loading installed plugins...": "正在加载已安装插件...",
    "Loading available plugins...": "正在加载可用插件...",
    "Loading customizations...": "正在加载定制项...",
    "Loading MCP servers...": "正在加载 MCP 服务器...",
    "Loading hooks...": "正在加载钩子...",
    "Loading models...": "正在加载模型...",
    "Loading conversations...": "正在加载对话...",
    "No Plugins Available": "暂无可用插件",
    "No plugins available.": "暂无可用插件。",
    "No matching plugins found.": "未找到匹配的插件。",
    "No customizations match your search.": "没有符合搜索条件的定制项。",
    "No skills available": "暂无可用技能",
    "Enable the plugin to sign in.": "请先启用该插件再进行登录。",
    "Enable this plugin to manage its accounts.": "启用此插件以管理其关联账户。",
    "Sign in to finish setting up this plugin.": "请登录以完成此插件的配置。",
    "Disabled. Open the plugin page to finish setup.": "已禁用。请打开插件页面完成配置。",
    "Disabled. Open Details to finish setup or enable.": "已禁用。请打开详情完成配置或启用。",
    "Install this plugin to see the commands it adds, along with its skills, agents and MCP servers.": "安装此插件以查看其提供的命令、技能、智能体和 MCP 服务器。",
    "Services this plugin connects to on your behalf. Credentials stay on this machine and are only sent to the domains listed.": "此插件代表您连接的服务。凭据仅保存在本机，且仅发送至所列域名。",
    "Managed by plugin": "由插件管理",
    "Connectors": "连接器",
    "Connections": "连接",
    "Search connectors": "搜索连接器",
    "Connect GitHub": "连接 GitHub",
    "Connect GitHub with the GitHub plugin": "通过 GitHub 插件连接 GitHub",
    "Connected Google Drive and GitHub resources": "已连接的 Google Drive 与 GitHub 资源",
    "Sign in to an app once and your agent can use it on any device. Open an app to see the account it uses or to disconnect it.": "只需登录一次应用，您的智能体即可在任意设备上调用。打开应用可查看关联账户或断开连接。",
    "Manage Hooks": "管理钩子 (Hooks)",
    "Agent Hooks Configuration": "智能体钩子配置",
    "Configure hooks that run on agent lifecycle events.": "配置在智能体生命周期事件触发时运行的钩子脚本。",
    "Add Hook Card": "添加钩子卡片",
    "Delete Hook": "删除钩子",
    "New hook name": "新钩子名称",
    "Add Handler": "添加处理器",
    "Delete Handler": "删除处理器",
    "Hook will trigger if any tool is executed.": "执行任意工具时均会触发该钩子。",
    "Refresh MCP servers": "刷新 MCP 服务器",
    "Delete MCP Server": "删除 MCP 服务器",
    "Delete Skill": "删除技能",
    "Search for MCP servers to add to your configuration": "搜索要添加到配置中的 MCP 服务器",
    "Enter the configuration values this MCP server needs. Saving restarts the server with them.": "输入此 MCP 服务器所需的配置参数，保存后将使用新配置重启该服务器。",
    "Ask the agent to diagnose and fix this server": "让智能体诊断并修复此服务器",
    "UI Extensions": "界面扩展",
    "UI extensions": "界面扩展",
    "Show or Hide Extensions": "显示或隐藏扩展",
    "Run a prompt on a schedule, like a morning summary of yesterday's changes. Runs show up here.": "按计划定时运行提示词（例如每天早上总结昨日变更），运行记录将显示在此处。",
    "Creates a local automation that runs on this computer": "创建在此电脑上运行的本地自动化任务",
    "Connect an account so the agent can run automations.": "连接账户以便智能体运行自动化任务。",
    "What should it do?": "需要执行什么任务？",
    "What should the agent do on each run?": "每次运行时智能体需要做什么？",
    "When should it run?": "何时运行？",
    "Where should it run?": "在哪里运行？",
    "When it runs": "运行时间",
    "When something happens": "当特定事件发生时",
    "On a schedule": "定时计划",
    "Add schedule": "添加计划",
    "Change schedule": "修改计划",
    "Custom schedule": "自定义计划",
    "Schedule": "计划日程",
    "Repeat every": "重复周期",
    "Every hour": "每小时",
    "Every day": "每天",
    "Every week": "每周",
    "Every weekday": "每个工作日",
    "Daily": "每天",
    "Days": "天数",
    "Last run": "上次运行",
    "Next run": "下次运行",
    "No runs yet": "暂无运行记录",
    "All runs": "全部运行记录",
    "Runs on this computer": "在此电脑上运行",
    "Prompt to run when triggered...": "触发时要执行的提示词...",
    "Refresh all credentials": "刷新全部凭据",
    "Side Question": "侧边提问",
    "Side Questions": "侧边提问",
    "New Side Question": "新建侧边提问",
    "Delete Side Question": "删除侧边提问",
    "Delete side question": "删除侧边提问",
    "Stop Side Question": "停止侧边提问",
    "Stop side question": "停止侧边提问",
    "Minimize side question": "最小化侧边提问",
    "Ask a quick question without interrupting the main conversation.": "在不打断主对话的情况下快速提问。",
    "Ask a side question without interrupting the main conversation": "在不打断主对话的情况下发起侧边提问",
    "Promote to conversation": "升级为独立对话",
    "Best of N": "多方案优选 (Best-of-N)",
    "Enable Best-of-2": "启用双方案对比 (Best-of-2)",
    "Number of responses": "生成回复数量",
    "Trigger multiple response variants from the same prompt.": "针对同一提示词并行生成多个候选回复以供优选。",
    "Use full Git clones for Best of N": "在多方案优选中使用完整 Git 克隆",
    "Use full VCS clones for Best of N": "在多方案优选中使用完整 VCS 克隆",
    "Fork": "创建分支对话",
    "Fork Conversation": "创建分支对话",
    "Fork conversation in this folder": "在当前文件夹创建分支对话",
    "Fork in New Workspace": "在新工作区创建分支对话",
    "Fork in Shared Workspace": "在共享工作区创建分支对话",
    "Pin This Conversation": "置顶此对话",
    "Unpin This Conversation": "取消置顶此对话",
    "Pinned Conversations": "已置顶对话",
    "Archive This Conversation": "归档此对话",
    "Rename This Conversation": "重命名此对话",
    "Rename Conversation": "重命名对话",
    "Mark This Conversation as Read": "标记此对话为已读",
    "Mark This Conversation as Unread": "标记此对话为未读",
    "Mark All as Read": "全部标为已读",
    "Mark as Read": "标为已读",
    "Mark as Unread": "标为未读",
    "Only Unread": "仅看未读",
    "Only Archived": "仅看已归档",
    "Archived Only": "仅已归档",
    "View archived in the sidebar": "在侧边栏查看已归档对话",
    "Move to Group": "移动到分组",
    "Move to New Group": "移动到新分组",
    "New Group": "新建分组",
    "Rename Group": "重命名分组",
    "Remove from Group": "从分组中移除",
    "Split Conversation Horizontally": "水平分屏对话",
    "Split Conversation Vertically": "垂直分屏对话",
    "Remove From Split": "退出分屏",
    "Remove from Split": "退出分屏",
    "Equalize Split Panes": "均分分屏面板宽度",
    "Open Conversation in New Tab": "在新标签页打开对话",
    "Open Conversation History": "打开对话历史",
    "Open Command Palette": "打开命令面板",
    "Open Keyboard Shortcuts": "打开键盘快捷键",
    "Open Workspace Selector": "打开工作区选择器",
    "Open Folder": "打开文件夹",
    "Open Folder (Interactive)": "打开文件夹（交互式）",
    "Open Terminal": "打开终端",
    "Open Search": "打开搜索",
    "Open in Built-in Browser": "在内置浏览器中打开",
    "Open Link in External Browser": "在外部浏览器中打开链接",
    "Open in Side Panel": "在侧边面板中打开",
    "Open in New Window": "在新窗口中打开",
    "Open in Antigravity IDE": "在 Antigravity IDE 中打开",
    "Switch IDE Workspace": "切换 IDE 工作区",
    "Toggle Side Panel": "切换侧边面板",
    "Toggle Overview Panel": "切换概览面板",
    "Toggle Terminal Panel": "切换终端面板",
    "Toggle Terminal": "切换终端",
    "Toggle File Viewer": "切换文件查看器",
    "Toggle Project Selector": "切换项目选择器",
    "Toggle Environment Selector": "切换环境选择器",
    "Toggle Maximize Side Panel": "最大化/还原侧边面板",
    "Close Sidebar": "关闭侧边栏",
    "Close Panel": "关闭面板",
    "New Tab": "新建标签页",
    "New tab": "新建标签页",
    "New Terminal Tab": "新建终端标签页",
    "Close Terminal Tab": "关闭终端标签页",
    "New Workspace": "新建工作区",
    "New Worktree": "新建工作树 (Worktree)",
    "Work in a New Worktree": "在新工作树中工作",
    "Select Worktree": "选择工作树",
    "Select Environment": "选择环境",
    "Select Project": "选择项目",
    "Select workspace": "选择工作区",
    "Local Windows environment": "本地 Windows 环境",
    "Add Shortcut": "添加快捷键",
    "Edit Shortcut": "编辑快捷键",
    "Remove Shortcut": "移除快捷键",
    "Reset All to Defaults": "全部重置为默认",
    "Reset all shortcuts to defaults": "将所有快捷键重置为默认值",
    "Search shortcuts": "搜索快捷键",
    "Press keys...": "请按下快捷键...",
    "Search Conversations": "搜索对话",
    "Search conversations...": "搜索对话...",
    "Search for conversations...": "搜索对话...",
    "Search for commands...": "搜索命令...",
    "Search file contents...": "搜索文件内容...",
    "Find in Conversation": "在对话中查找",
    "Copy Conversation Markdown": "复制对话为 Markdown",
    "Conversation copied as Markdown to clipboard": "已将对话以 Markdown 格式复制到剪贴板",
    "Copy Message": "复制消息",
    "Copy Command": "复制命令",
    "Copy Content": "复制内容",
    "Copy File Name": "复制文件名",
    "Copy File Path": "复制文件路径",
    "Copy Path": "复制路径",
    "Copy Link Address": "复制链接地址",
    "Copy Image": "复制图片",
    "Path copied!": "路径已复制！",
    "Copied": "已复制",
    "Add to Chat": "添加到对话",
    "Terminal: Add to Chat": "终端：添加到对话",
    "Insert in Terminal": "插入到终端",
    "Insert in terminal": "插入到终端",
    "Quote Selection": "引用选中内容",
    "Comment on Selection": "评论选中内容",
    "Proceed with Plan": "按计划继续执行",
    "Accept Step": "接受此步",
    "Reject Step": "拒绝此步",
    "Cancel Step": "取消此步",
    "Cancel Generation": "取消生成",
    "Cancel Task": "取消任务",
    "Cancel All Tasks": "取消全部任务",
    "Stop All Subagents": "停止所有子智能体",
    "Stop Subagent": "停止子智能体",
    "Stop execution": "停止执行",
    "Continue Response": "继续生成回复",
    "Undo to Here": "撤销至此处",
    "Upload Files": "上传文件",
    "Download File": "下载文件",
    "Download PDF": "下载 PDF",
    "Export as PDF": "导出为 PDF",
    "Start Voice Recording": "开始语音录制",
    "Stop Voice Recording": "停止语音录制",
    "Voice Mode": "语音模式",
    "Microphone": "麦克风",
    "Input device for voice mode and dictation.": "用于语音模式与语音听写的输入设备。",
    "Changes": "变更",
    "Staged Changes": "已暂存变更",
    "Branch Changes": "分支变更",
    "Stage change": "暂存更改",
    "Unstage change": "取消暂存",
    "Discard unstaged changes": "放弃未暂存更改",
    "Revert file changes": "还原文件更改",
    "Commit": "提交",
    "Amend": "修正提交 (Amend)",
    "Push": "推送",
    "Branch": "分支",
    "Untracked": "未跟踪",
    "Modified": "已修改",
    "Uncommitted": "未提交",
    "Expand All Folders": "展开全部文件夹",
    "Collapse All Folders": "折叠全部文件夹",
    "No file changes": "暂无文件变更",
    "No active terminals": "暂无活动终端",
    "No active terminals. Click + to create one.": "暂无活动终端，点击 + 新建终端。",
    "No background tasks": "暂无后台任务",
    "No browser pages open": "暂无打开的浏览器页面",
    "No recent downloads": "暂无最近下载",
    "No uploads": "暂无上传文件",
    "Files modified by the agent in this conversation": "本次对话中智能体修改的文件",
    "Artifact updated by agent": "智能体已更新产物",
    "The conversation was compacted to fit within the context window.": "对话已自动压缩以适应上下文窗口。",
    "This command ran in the sandbox.": "此命令已在安全沙盒中运行。",
    "Confirm the command is safe to run outside of the sandbox with full network and disk access.": "请确认该命令在沙盒外运行是安全的（将拥有完整网络和磁盘访问权限）。",
    "Browser Subagent": "浏览器子智能体",
    "Browser Subagent Viewer": "浏览器子智能体视图",
    "Capture Screenshot": "截取屏幕截图",
    "Add screenshot to conversation": "将截图添加到对话",
    "Reload Window": "重新加载窗口",
    "Reload app": "重新加载应用",
    "Got it": "知道了",
    "Try Again": "重试",
    "Try again": "重试",
    "Proceed Anyway": "仍然继续",
    "More Actions": "更多操作",
    "More actions": "更多操作",
    "More options": "更多选项",
    "Sort By": "排序方式",
    "Prevent system sleep when agent is active.": "当智能体处于活动状态时阻止系统休眠。",
    "Keep computer awake while the agent is running tasks.": "当智能体正在执行任务时保持计算机处于唤醒状态。",
    "Keep Computer Awake": "保持电脑唤醒",
    "Keep computer awake": "保持电脑唤醒状态",
    "Run in the background when window is closed.": "关闭窗口后在后台继续运行。",
    "Run in Background": "后台运行",
    "Run in background": "后台静默运行",
    "Automatically download and install updates": "自动下载并安装更新",
    "Automatically check for updates.": "自动检查更新。",
    "Auto Check for Updates": "自动检查更新",
    "Auto check for updates": "自动检查更新",
    // Top Bar & Global Navigation
    "Goals": "目标", "Tasks": "任务", "Artifacts": "产物", "Artifact": "产物", "Scratch": "草稿", "Chat": "对话",
    "No artifacts generated": "暂无生成的产物", "No artifacts": "暂无产物",
    "Active": "进行中", "Inactive": "未激活", "Completed": "已完成", "Failed": "已失败",
    "History": "历史记录", "Settings": "设置", "System": "系统", "Network": "网络",
    "Model": "模型", "Memory": "记忆", "Tools": "工具", "Agents": "智能体",
    "Overview": "概览", "Logs": "日志", "Clear": "清除", "Save": "保存",
    "Cancel": "取消", "Submit": "提交", "Run": "运行", "Stop": "停止",
    "Edit": "编辑", "Delete": "删除", "Add": "添加", "Remove": "移除", "Download": "下载",
    "Monthly Limit": "每月限额", "Weekly Limit": "每周限额", "Five Hour Limit": "五小时限额",
    "Weekly Limit Remaining": "每周限额剩余", "Five Hour Limit Remaining": "五小时限额剩余",
    "limit": "限额", "limits": "限额", "weekly": "每周", "hourly": "每小时",
    "Sidebar": "侧边栏", "Display Options": "显示选项", "Message input": "消息输入框", "Record voice memo": "录制语音备忘",
    "Typeahead menu": "预输入菜单", "Group By": "分组方式", "Last Updated": "最后更新", "Last Prompt": "最新提示词", "Last prompt": "最新提示词",
    "Alphabetical (A-Z)": "字母顺序 (A-Z)", "Alphabetical (Z-A)": "字母倒序 (Z-A)", "Date Added": "添加日期", "Creation Date": "创建日期", "Created Date": "创建日期", "Subtitles": "副标题", "No Subtitle": "无副标题",
    "Filter": "筛选", "Scheduled": "已计划", "Environment": "环境", "None": "无", "Fast": "快速",
    "Last 7 days": "最近 7 天", "Last 24 hours": "最近 24 小时", "Last 30 days": "最近 30 天", "Last 3 months": "最近 3 个月",
    "Today": "今天", "Yesterday": "昨天", "This week": "本周", "This month": "本月", "All time": "全部时间",
    "Project": "项目", "project": "项目", "projects": "项目", "Conversation": "对话", "conversation": "对话",
    "No Project": "无项目", "No project": "无项目", "no project": "无项目",
    "No projects found": "暂无项目", "No projects found.": "暂无项目",
    "No project found": "暂无项目", "No project found.": "暂无项目",
    "found": "找到", "not found": "未找到", "Not found": "未找到",
    "Search projects": "搜索项目", "Search projects...": "搜索项目...",
    "Workspace": "工作区", "workspace": "工作区", "Minimize": "最小化", "Maximize": "最大化", "Back": "返回",
    "Folders": "文件夹", "folders": "文件夹", "including": "包括",
    "Rename": "重命名", "Mark Unread": "标记为未读", "Mark Read": "标记为已读", "Duplicate": "制作副本",
    "Export": "导出", "Import": "导入", "Pin": "置顶", "Archive": "归档",
    "Split": "分屏", "Split Right": "向右分屏", "Split Down": "向下分屏", "Split Left": "向左分屏", "Split Up": "向上分屏",
    "Replace With New": "替换为新建", "Replace with New": "替换为新建", "Replace with new": "替换为新建",
    "Copy Link": "复制链接", "Copy link": "复制链接", "Copy ID": "复制 ID", "Copy id": "复制 ID",
    "Copy Conversation ID": "复制对话 ID", "Copy Conversation Link": "复制对话链接", "Duplicate Conversation": "复制对话",
    "Close Others": "关闭其他", "Close All": "全部关闭", "Close to the Right": "关闭右侧", "Close Saved": "关闭已保存",
    "Create New Project": "创建新项目", "Archive Conversation": "归档对话", "now": "刚刚",
    "Conversation Name": "对话名称", "Conversation ID": "对话 ID", "Project Name": "项目名称",
    "Toggle Auxiliary Pane": "切换辅助面板", "Maximize Pane": "最大化面板", "Minimize Pane": "最小化面板", "Restore Pane": "还原面板",
    "Files Changed": "已修改文件", "Files changed": "已修改文件", "File Changed": "已修改文件",
    "Uploads": "已上传文件", "uploads": "已上传文件", "See all": "查看全部", "See All": "查看全部",
    "Background Tasks": "后台任务", "Background tasks": "后台任务", "Background Task": "后台任务",
    "Terminals": "终端", "terminals": "终端", "Delete Terminal": "删除终端", "Split Terminal": "拆分终端",
    "Add Terminal": "添加终端", "Add terminal": "添加终端",
    "No subagents": "暂无子智能体", "No subagents running": "暂无运行中的子智能体", "No subagent": "暂无子智能体",
    "Select Model": "选择模型", "Select model": "选择模型", "Select a model": "选择一个模型",
    "User cancelled agent execution.": "用户取消了智能体执行。",
    "Open Antigravity IDE": "打开 Antigravity IDE", "Create Project": "创建项目", 
    "Command Palette": "命令面板", "Zoom In": "放大", "Zoom Out": "缩小", "Reset Zoom": "重置缩放",
    "Delete Conversation": "删除对话", "Are you sure you want to delete this conversation? This action cannot be undone.": "您确定要删除此对话吗？此操作无法撤销。",
    "Confirm Undo": "确认撤销", "This undo action will not make any code changes.": "此撤销操作不会对代码做出任何更改。",
    "Confirm Redo": "确认重做", "This redo action will not make any code changes.": "此重做操作不会对代码做出任何更改。",
    "Undo changes up to this point": "撤销更改至此处", "Redo changes up to this point": "重做更改至此处",
    "Confirming this undo action will make the following changes:": "确认此撤销操作将做出以下更改：",
    "Confirming this undo action will not make any code changes.": "确认此撤销操作不会做出任何代码更改。",
    "Confirming this redo action will make the following changes:": "确认此重做操作将做出以下更改：",
    "Confirming this redo action will not make any code changes.": "确认此重做操作不会做出任何代码更改。",
    "Undo changes": "撤销更改", "Redo changes": "重做更改",
    "Record Audio": "录制音频", "Record Audio Ctrl+M": "录制音频 Ctrl+M",
    "Send message": "发送消息", "Send message Enter": "发送消息 Enter",
    "Getting started with a Project": "开始使用项目",
    "Now that you've created a project, configure your project's agent settings or start a conversation.": "现在您已经创建了一个项目，接下来请配置该项目的智能体设置，或者直接开始对话。",
    "Open Settings": "打开设置", "Start first conversation": "开始首次对话",
    "Main Agent": "主智能体", "Add Context": "添加上下文",
    "Loading Antigravity": "正在加载 Antigravity", "Loading": "正在加载",
    "+ New Conversation": "+ 新建对话", "New Conversation": "新建对话", "Conversation History": "历史对话", "Scheduled Tasks": "计划任务",
    "Automations": "自动化", "Automation": "自动化",
    "Open File": "打开文件", "New Terminal": "新建终端", "just now": "刚刚", "Just now": "刚刚",
    "No conversations yet": "暂无对话", "Open IDE": "打开 IDE", "Window": "窗口",
    "Review": "审阅", "Email": "电子邮箱", "Upgrade": "升级", "Not in Project": "未分组项目",
    "Ask anything, @ to mention, / for actions": "输入任何问题，使用 @ 提及，使用 / 执行操作",
    "Status": "状态", "Sort Conversations": "对话排序", "Worktree": "工作区树",
    "New Project": "新建项目", "Quick Start": "快速开始",
    "Good response": "好的回答", "Bad response": "差的回答",

    // General Settings Page
    "General": "常规", "Appearance": "外观", "Theme": "主题", "Light": "浅色", "Dark": "深色",
    "Language": "语言", "Version": "版本", "Check for Updates": "检查更新", "About": "关于",
    "Advanced": "高级", "API Key": "API 密钥", "Account": "账号", "Profile": "个人资料",
    "Logout": "退出登录", "Sign Out": "退出登录", "Feedback": "反馈", "Privacy": "隐私",
    "Terms": "条款", "Auto-start": "开机自启", "Launch on startup": "开机时启动",
    "Notifications": "通知", "Shortcuts": "快捷键", "Keyboard Shortcuts": "键盘快捷键",
    "Global Shortcut": "全局快捷键", "Toggle Visibility": "切换显示/隐藏", "Proxy": "代理",
    "Update": "更新", "Updates": "更新", "Check for update": "检查更新",
    "Models": "模型", "Customizations": "自定义", "Browser": "浏览器", "App": "应用", "Application": "应用", "Applications": "应用",
    "Projects": "项目", "Conversations": "对话", "Provide Feedback": "提供反馈",
    "Manage your plan, credentials, and general preferences.": "管理您的套餐、凭据和常规偏好设置。",
    "Enable Telemetry": "启用遥测",
    "When toggled on, Antigravity collects usage data to help Google enhance performance and features.": "开启后，Antigravity 将收集使用数据，以帮助 Google 提升性能和功能。",
    "Marketing Emails": "营销邮件",
    "Receive product updates, tips, and promotions from Google Antigravity via email.": "通过电子邮件接收来自 Google Antigravity 的产品更新、提示和促销信息。",
    "Your Plan: Google AI Pro": "当前计划：Google AI Pro", "Your Plan:": "当前计划：",
    "You can upgrade to a Google AI Ultra plan to receive higher rate limits.": "您可以升级至 Google AI Ultra 套餐以获得更高的使用限额。",
    "By using this app, you agree to its ": "使用本应用即表示您同意其 ",
    "Terms of Service": "服务条款",
    "Configure agent execution, queued message delivery, and permissions.": "配置智能体执行、排队消息发送以及权限。",
    "Execution": "执行", "Agent Settings": "智能体设置", "Agent Behavior": "智能体行为",
    "File Permissions": "文件权限", "Network Permissions": "网络权限",
    "Queued Messages": "排队消息", "Configure when follow-up messages are sent.": "配置发送后续消息的时机。",
    "Queue": "排队", "Send Immediately": "立即发送", "Keyboard shortcuts": "键盘快捷键",
    "Security Preset": "安全预设", 
    "Choose a predefined security preset for the agent. This controls terminal auto-execution policy, and file access policy.": "为智能体选择一个预定义的安全预设。这将控制终端自动执行策略和文件访问策略。",
    "Controls the actions the agent can take.": "控制智能体可以执行的操作。",
    "Controls the actions the agent can take": "控制智能体可以执行的操作",
    "Global Permissions": "全局权限", "Global permissions": "全局权限",
    "Tool Permissions": "工具权限", "Tool permissions": "工具权限",
    "Modify permissions for file, terminal, and MCP tools.": "修改文件、终端和 MCP 工具的权限。",
    "Modify permissions for file, terminal, and MCP tools": "修改文件、终端和 MCP 工具的权限",
    "Default": "默认", "Always Ask": "总是询问", "Always Proceed": "自动执行",
    "Inherit Global": "继承全局", "Inherits Global": "继承全局", "inherit global": "继承全局",
    "Inherits your Global Permissions when working in this project.": "在此项目中工作时继承您的全局权限。",
    "Inherits your Global Permissions when working in this project": "在此项目中工作时继承您的全局权限",
    "Inherits your Global Permissions": "继承您的全局权限",
    "Plan Review Policy": "计划审阅策略",
    "Whether the agent asks you to review its documents.": "智能体是否要求您审阅其文档。",
    "Whether the agent asks you to review its documents": "智能体是否要求您审阅其文档",
    "Type / and select plan to have the agent generate a plan.": "输入 / 并选择 plan 即可让智能体生成计划。",
    "Type / and select plan to have the agent generate a plan": "输入 / 并选择 plan 即可让智能体生成计划",
    "to have the agent generate a plan.": "即可让智能体生成计划。",
    "to have the agent generate a plan": "即可让智能体生成计划",
    "and select": "并选择",
    "Artifact Review Policy": "产物审阅策略",
    "Specifies Agent's behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience.": "指定智能体在请求审阅产物时的行为。产物是指其为提供更丰富对话体验而创建的各类文档与生成物。",
    "File Access Rules": "文件访问规则", "Configure allowed and denied paths for file reads and writes.": "配置允许和拒绝的文件读取和写入路径。",
    "Network Access Rules": "网络访问规则", "Configure allowed and denied URLs for reading.": "配置允许和拒绝读取的 URL。",
    "File Reads": "文件读取", "Allow/deny agent read access to specific files or directories.": "允许/拒绝智能体对特定文件或目录的读取权限。",
    "File Writes": "文件写入", "Allow/deny agent write access to specific files or directories.": "允许/拒绝智能体对特定文件或目录的写入权限。",
    "Network Reads": "网络读取", "Allow/deny agent read access to specific URLs.": "允许/拒绝智能体对特定 URL 的读取权限。",
    "Read URLs": "URL 读取", "Allow/deny agent read access to specific URLs or domains.": "允许/拒绝智能体对特定 URL 或域名的读取权限。",
    "Allow/deny specific terminal commands.": "允许/拒绝特定的终端命令。", "e.g., npm test": "例如：npm test",
    "External tools the agent can call via Model Context Protocol.": "智能体可通过模型上下文协议 (MCP) 调用的外部工具。", "Enter tool name or server...": "输入工具名称或服务器...",
    "Allow/deny agent command execution outside the sandbox.": "允许/拒绝智能体在沙盒外部执行命令。", "e.g., curl": "例如：curl",
    "Allow": "允许", "Deny": "拒绝", "There are no customizations enabled.": "当前未启用任何自定义项。",
    "Manage Antigravity app settings.": "管理 Antigravity 应用设置。",
    "Inherits your General settings when working in this project.": "在此项目中工作时继承您的全局设置。",
    "No MCP servers installed": "未安装任何 MCP 服务器", "Use Add MCP to browse the store, or add a custom server via the MCP config.": "使用“添加 MCP”浏览商店，或通过 MCP 配置添加自定义服务器。",
    "Plugins": "插件", "Browse and enable plugins from the Build With Google catalog.": "浏览并启用“使用 Google 构建”目录中的插件。",
    "Cloud CLI MCP Server provides tools to run gcloud and bq CLIcommands in a remote sandbox environment": "Cloud CLI MCP 服务器提供了在远程沙盒环境中运行 gcloud 和 bq CLI 命令的工具。",
    "Browser Actuation Permissions": "浏览器操作权限", "Execute URLs": "URL 执行", "Allow/deny agent browser actuation access to specific URLs.": "允许/拒绝智能体对特定 URL 的浏览器操作权限。",
    "Media": "媒体", "Mentions": "提及", "Actions": "操作",
    "Enable Remote Control": "启用远程控制", "Work with local agents from another device.": "在其他设备上与本地智能体协同工作。",
    "Enter Queues after the turn": "Enter 键：在当前轮次后排队",
    "Alt+Enter Sends immediately": "Alt+Enter 键：立即发送",
    "Alt+Enter On empty prompt, sends next in queue": "Alt+Enter 键：在输入为空时，发送队列中的下一条",
    "Useful for typical development with an emphasis on security. It prioritizes safety over speed by requiring manual approval for all terminal commands and files outside the project directory.": "适用于注重安全的典型开发场景。它将安全性置于速度之上，要求对所有终端命令和项目目录之外的文件访问进行手动批准。",
    "Requires manual review for all terminal commands and file accesses outside of the working folders.": "要求对所有终端命令和工作文件夹之外的文件访问进行手动审阅。",
    "Full machine": "完整机器访问",
    "All terminal commands require review. The agent can read or write to any file in the machine.": "所有终端命令均需审阅。智能体可以读取或写入机器上的任何文件。",
    "Turbo mode": "极速模式",
    "Disables all safety barriers for maximal iteration velocity.": "禁用所有安全屏障，以获得最快的迭代速度。",
    "Custom": "自定义配置", "Manually customize individual settings.": "手动自定义各项设置。",
    "System Default": "跟随系统", "Zoom Level": "缩放比例", "Font Size": "字体大小",
    "Small": "小", "Medium": "中", "Large": "大", "Code Font": "代码字体", "Editor Font": "编辑器字体",
    "Default Model": "默认模型", "Temperature": "温度", "System Prompt": "系统提示词",
    "Search Engine": "搜索引擎", "Web Search": "网络搜索", "Enable Web Access": "启用网络访问",
    "Startup": "启动", "Launch at login": "登录时自动启动", "Hardware Acceleration": "硬件加速",
    "Current Version": "当前版本", "Up to date": "已是最新版本", "Downloading": "下载中...",
    "Restart to update": "重启以更新", "Danger Zone": "危险区域", "Clear History": "清除历史记录",
    "Delete All": "全部删除", "Reset to Default": "恢复默认设置", "Restore Defaults": "恢复默认设置", "Reset to default": "恢复默认", "Restore defaults": "恢复默认设置",
    "Keybindings": "快捷键绑定", "Command": "命令", "Shortcut": "快捷键", "Action": "操作",
    "Advanced Settings": "高级设置", "Developer Tools": "开发者工具", "Toggle Developer Tools": "切换开发者工具",
    "Open Logs": "打开日志", "Proxy Server": "代理服务器", "Enable Proxy": "启用代理",
    "Auto-Updater": "自动更新程序", "Always": "始终", "Never": "从不", "Ask": "询问",
    "Contrast": "对比度", "contrast": "对比度", "Strong": "强", "strong": "强",
    "Windows Subsystem for Linux": "适用于 Linux 的 Windows 子系统 (WSL)",
    "Run the app against a Linux environment. Connecting relaunches the app into the selected WSL distro.": "在 Linux 环境中运行应用。连接后将重启应用并切换至所选的 WSL 分发版。",
    "Connect": "连接", "connect": "连接",
    "App version": "应用版本", "App Version": "应用版本",
    "Automatic Check for Updates": "自动检查更新",
    "Automatically prompt you to restart the app when a new update is available. When disabled, you can check for updates manually from the app menu.": "当有新更新可用时自动提示您重启应用。禁用后，您可以从应用菜单中手动检查更新。",
    "Invalid Media": "无效媒体", "invalid media": "无效媒体",
    "Maximum number of attachments reached": "已达到附件数量上限",
    "Maximum number of attachments reached.": "已达到附件数量上限。",
    "Save changes": "保存更改", "Apply": "应用", "OK": "确定", "Features": "功能",
    "Experimental Features": "实验性功能", "Enable": "启用", "Disable": "禁用",
    "API Configuration": "API 配置", "Account Settings": "账号设置", "Profile Settings": "个人资料",
    "Workspace Settings": "工作区设置", "Manage Projects": "管理项目",
    "Terminal & Tooling Permissions": "终端与工具权限",
    "Terminal Commands": "终端命令", "Configure allowed terminal commands.": "配置允许执行的终端命令。",
    "Commands Outside Sandbox": "沙盒外命令", "Configure allowed commands outside the sandbox.": "配置允许在沙盒外执行的命令。",
    "MCP Tools": "MCP 工具", "Configure external tools via Model Context Protocol.": "通过模型上下文协议配置外部工具。",
    "Allow write access to this path?": "允许对此路径写入吗？", "Yes, allow this time": "是，仅允许本次",
    "Yes, and always allow in this conversation": "是，并在本次对话中始终允许",
    "Yes, and always allow when not in a project": "是，并在非项目中始终允许",
    "Yes, and always allow": "是，始终允许", "No (tell the agent what to do instead)": "否 (告诉智能体改做什么)",
    "Skip": "跳过", "Submit": "提交",

    // Models & Usage Tab
    "Models & Usage": "模型与用量", "Manage your model quota and credits.": "管理您的模型配额和积分额度。",
    "Plan": "订阅计划", "Model Credits": "模型积分", "Enable AI Credit Overages": "启用 AI 积分超额使用",
    "When toggled on, Antigravity will use your AI credits to fulfill model requests once you're out of model quota. Antigravity will always use your model quota first before using AI credits.": "启用后，当您的模型配额用尽时，Antigravity 将使用您的 AI 积分来完成模型请求。Antigravity 将始终优先使用模型配额。",
    "See Activity": "查看活动", "Get More AI Credits": "获取更多 AI 积分",
    "Available AI Credits:": "可用 AI 积分：",
    "Gemini Models": "Gemini 模型", "Claude and GPT models": "Claude 和 GPT 模型",
    "Limited time": "限时", "Low": "低", "High": "高", "View Usage": "查看用量",
    "Notice": "提示", "notice": "提示", "Leaving Soon": "即将下线", "Leaving soon": "即将下线",
    "Start using Gemini 3.8 Flash, our best Flash model.": "开始使用 Gemini 3.8 Flash，我们最强大的 Flash 模型。",
    "Sonnet 5.5 is now available on paid Pro and Ultra plans. Third-party model access will no longer be available on your current plan starting on November 2, 2026.": "Sonnet 5.5 现已在付费的 Pro 和 Ultra 方案中提供。从 2026 年 11 月 2 日起，您当前的方案将不再支持访问第三方模型。",

    // Customizations & Plugins
    "Configure default behaviors, skills, and MCP servers.": "配置默认行为、技能和 MCP 服务器。",
    "Learn more.": "了解更多。", "Learn more": "了解更多",
    "Token Usage": "Token 使用量",
    "The breakdown below shows token usage from customizations like rules, skills, and MCP. If a budget is exceeded, large rules are demoted to path pointers and large customizations are excluded automatically.": "下方的明细展示了来自规则、技能和 MCP 等自定义项的 Token 使用情况。如果超出预算，大型规则将降级为路径指针，大型自定义项将被自动排除。",
    "The breakdown below shows token usage from customizations like skills, rules, and MCP. If the budget is exceeded, large customizations will be truncated automatically.": "下方的明细展示了来自技能、规则和 MCP 等自定义项的 Token 使用情况。如果超出预算，大型规则将降级为路径指针，大型自定义项将被自动排除。",
    "Skills": "技能", "Rules": "规则",
    "Installed MCP Servers": "已安装的 MCP 服务器",
    "Add MCP +": "添加 MCP +", "Add MCP": "添加 MCP", "Add MCP Servers": "添加 MCP 服务器", "Add MCP Server": "添加 MCP 服务器",
    "Copy Config File Path": "复制配置文件路径",
    "Search MCP servers by name": "按名称搜索 MCP 服务器",
    "Refresh": "刷新", "Refreshing...": "刷新中...", "Refreshing": "刷新中",
    "Analyzed": "已分析", "analyzed": "已分析",
    "Exploring file, editing file": "浏览文件、编辑文件",
    "Open MCP Config": "打开 MCP 配置",
    "No MCP Servers": "无 MCP 服务器",
    "You currently don't have any MCP Servers installed. Add an MCP server above or add a custom one via the MCP Config.": "您目前尚未安装任何 MCP 服务器。请在上方添加 MCP 服务器，或通过 MCP 配置添加自定义服务器。",
    "Build With Google Plugins": "使用 Google 插件构建", "Build with Antigravity Plugins": "使用 Antigravity 插件构建",
    "Customize": "自定义", "Hide breakdown": "隐藏明细",
    "coding agent": "编程智能体",
    "Search customizations...": "搜索自定义项...",
    "Google Workspace": "Google Workspace",
    "Build with Google": "使用 Google 构建",
    "Marketplace": "插件市场",
    "Installed": "已安装",
    "Find skills, agents, and more in the Marketplace.": "在插件市场中发现技能、智能体及更多内容。",
    "Browse the Marketplace": "浏览插件市场",
    "Skills & Rules": "技能与规则",
    "Built In": "内置",
    "Custom Agents": "自定义智能体",
    "No custom agents yet.": "暂无自定义智能体。",
    "MCP Servers": "MCP 服务器",
    "No MCP servers yet. Use Add to browse the store.": "暂无 MCP 服务器。请使用“添加”浏览商店。",
    "Create a Plugin with the Agent": "使用智能体创建插件",
    "See less": "收起",
    "Google Docs": "Google 文档",
    "Google Sheets": "Google 表格",
    "Google Slides": "Google 幻灯片",
    "Google Drive": "Google 云端硬盘",
    "Google Calendar": "Google 日历",
    "Gemini API": "Gemini API",
    "Android CLI": "Android CLI",
    "Data Agent Kit": "Data Agent Kit",
    "Dart and Flutter": "Dart 和 Flutter",
    "Google Maps Platform": "Google Maps Platform",
    "Core tools and knowledge required to develop for Android": "开发 Android 所需的核心工具和知识",
    "Modern Web Guidance": "现代 Web 开发指南",
    "Keep your coding agent up to date with the latest web best practices.": "让您的编程智能体掌握最新的 Web 最佳实践。",
    "Google Antigravity SDK": "Google Antigravity SDK",
    "Using the Antigravity Python SDK to build AI agents": "使用 Antigravity Python SDK 构建 AI 智能体",
    "Science": "科学", "Curated collection of agent skills for science.": "精选的科学领域智能体技能集合。",
    "Firebase": "Firebase",
    "Prototype, build & run modern apps users love with Firebase's backend, AI, and operational infrastructure.": "借助 Firebase 的后端、AI 和运营基础设施，设计原型、构建并运行深受用户喜爱的现代应用。",
    "Chrome DevTools": "Chrome 开发者工具",
    "Reliable automation, in-depth debugging, and performance analysis in Chrome using Chrome DevTools and Puppeteer": "使用 Chrome DevTools 和 Puppeteer 在 Chrome 中实现可靠的自动化、深度调试和性能分析",
    "Google Kubernetes Engine (Remote)": "Google Kubernetes Engine (远程)",

    // Shortcuts Panel
    "Configure keyboard shortcuts.": "配置键盘快捷键。",
    "Keyboard shortcuts for quick navigation and control.": "用于快速导航和控制的键盘快捷键。",
    "RECOMMENDED": "推荐", "NAVIGATION": "导航", "Recommended": "推荐", "Navigation": "导航",
    "Open Conversation Picker": "打开对话选择器", "Open File Search": "打开文件搜索",
    "Focus Input": "聚焦输入框", "File Picker": "文件选择器",
    "Select Previous Conversation": "选择上一个对话", "Select Next Conversation": "选择下一个对话",
    "Previous Pane Tab": "上一个面板标签", "Next Pane Tab": "下一个面板标签",
    "Toggle Model Selector": "切换模型选择器", "Toggle Voice Recording": "切换语音录制",
    "Find in Pane": "在面板中查找", "Add to Chat/Quote": "添加到对话/引用",
    "LAYOUT CONTROLS": "布局控制", "Layout Controls": "布局控制", "Layout controls": "布局控制",
    "App Shortcuts": "应用快捷键", "Editor Shortcuts": "编辑器快捷键", 
    "Global Shortcuts": "全局快捷键", "Terminal Shortcuts": "终端快捷键", 
    "Chat Shortcuts": "对话快捷键", "Press desired key combination": "按下所需的组合键",

    // Feedback Panel
    "Feedback Type": "反馈类型", "Auth and Billing": "认证与计费", "Description": "描述",
    "Please describe the issue in detail. The more actionable your feedback, the quicker our team can address your request. Some helpful information includes:": "请详细描述您的问题。您的反馈越具体，我们的团队就能越快处理您的请求。一些有用的信息包括：",
    "Steps to reproduce the issue": "重现问题的步骤", "Expected behavior": "预期行为",
    "Actual behavior": "实际行为", "Any error messages": "任何错误消息", "Any relevant information": "任何相关信息",
    "Describe the bug you encountered...": "描述您遇到的错误...",
    "Steps to Reproduce": "重现步骤", "Please list the steps to reproduce the issue...": "请列出重现问题的步骤...",
    "Please list the steps to reproduce the issue": "请列出重现问题的步骤",
    "Attach a screenshot (optional)": "附加截图（可选）", "Attach Antigravity server logs": "附加 Antigravity 服务器日志",
    "We'd love to hear from you.": "我们期待您的反馈。", "How can we improve?": "我们该如何改进？",
    "Thinking...": "思考中...", "Thought": "思考过程", "Agent is thinking...": "智能体正在思考...",
    "Show thought process": "显示思考过程", "Hide thought process": "隐藏思考过程",
    "Generating...": "生成中...", "Planning...": "计划中...",
    "Issue Type": "问题类型", "Bug Report": "错误报告", "Feature Request": "功能请求",
    "Remote Control Issue": "远程控制问题", "Remote control issue": "远程控制问题",
    "Legal Help": "法律帮助", "legal help": "法律帮助",
    "Visit Legal Help to ask for content changes for legal reasons.": "访问法律帮助以出于法律原因请求更改内容。",
    "Visit Legal Help to ask for content changes for legal reasons": "访问法律帮助以出于法律原因请求更改内容",
    "to ask for content changes for legal reasons.": "以出于法律原因请求更改内容。",
    "to ask for content changes for legal reasons": "以出于法律原因请求更改内容",
    "General Feedback": "常规反馈", "Describe your issue or idea...": "描述您的问题或想法...",
    "Please provide details...": "请提供详细信息...", "Include diagnostic data": "包含诊断数据",
    "Include app logs": "包含应用日志", "Send Feedback": "发送反馈",

    // Browser Tab
    "Browser Settings": "浏览器设置", "Configure the browser subagent. It requires": "配置浏览器子智能体。需要安装",
    "to be installed. The browser subagent can be invoked by typing /browser in the conversation input box.": "。您可以在对话输入框中输入 /browser 来调用浏览器子智能体。",
    "Browser Javascript Execution Policy": "浏览器 JavaScript 执行策略",
    "Controls whether the agent can run custom JavaScript to automate complex browser actions.": "控制智能体是否可以运行自定义 JavaScript 来自动化复杂的浏览器操作。",
    "Disabled": "已禁用", "Block all browser JavaScript execution.": "阻止所有浏览器 JavaScript 执行。",
    "Request Review": "请求审阅", "Prompt for approval before running browser scripts.": "在运行浏览器脚本前提示批准。",
    "Allow full browser script execution without prompting.": "允许执行完整的浏览器脚本而不提示。",
    "Actuation Permissions": "操作权限", "Browser Actuation Rules": "浏览器操作规则",
    "Configure allowed and denied URLs for browser actuation.": "配置允许和拒绝进行浏览器操作的 URL。",

    // App Tab
    "App Settings": "应用设置", "Manage application settings.": "管理应用设置。",
    "Prevent Sleep": "阻止睡眠", "Prevent the computer from sleeping while the app is running.": "在应用运行时阻止计算机进入睡眠状态。",
    "Keep In Menu Bar": "保留在系统托盘", 
    "The app will be accessible from the menu bar and will keep running in the background when all windows are closed.": "应用将可以从系统托盘访问，并在所有窗口关闭时继续在后台运行。",
    "Keep the app accessible from the menu bar and running in the background when all windows are closed.": "应用将可以从系统托盘访问，并在所有窗口关闭时继续在后台运行。",
    "Notification Settings": "通知设置", "To modify notification settings, open your operating system's system preferences.": "要修改通知设置，请打开操作系统的系统偏好设置。",
    "Open System Preferences": "打开系统偏好设置",

    // Conversations Tab & Permissions
    "Agent settings and permissions for conversations outside of projects.": "针对项目外对话的智能体设置和权限。",
    "Inherit General": "继承全局设置", "Local Permissions": "本地权限",
    "Also includes": "还包括", "global settings": "全局设置",
    "when working in this project.": "（当在此项目中工作时）。",
    "Toggle Sidebar": "切换侧边栏", "View Split Diff": "分屏查看差异", "Collapse All": "全部折叠",
    "Learn more about": "了解更多关于",
    "Configure the agent's visual theme and display preferences.": "配置智能体的视觉主题和显示偏好。",
    "Chat Settings": "聊天设置", "Verbose Agent Chat": "详细的智能体对话",
    "Display and preserve intermediate thinking steps.": "显示并保留中间思考过程。",
    "Conversation Width": "对话宽度", "Configure the maximum width of the conversation panel.": "配置对话面板的最大宽度。",
    "Narrow": "较窄", "Wide": "较宽",
    "Select light, dark, or inherit system settings.": "选择浅色、深色，或跟随系统设置。",
    "Light Theme": "浅色主题", "Preset": "预设", "Default Light": "默认浅色",
    "Background": "背景颜色", "Foreground": "前景颜色", "Accent": "强调色",
    "Dark Theme": "深色主题", "Default Dark": "默认深色",
    "Allow write access to this path?": "允许写入此路径吗？",
    "Allow read access to this path?": "允许读取此路径吗？",
    "Allow execution of this command?": "允许执行此命令吗？",
    "Yes, allow this time": "是，仅本次允许",
    "Yes, and always allow in this conversation": "是，在本次对话中始终允许",
    "Yes, and always allow when not in a project": "是，在未分组项目中始终允许",
    "Yes, and always allow": "是，始终允许",
    "tell the agent what to do instead": "告诉智能体接下来该做什么",
    "(tell the agent what to do instead)": "(告诉智能体接下来该做什么)",
    "Skip": "跳过", "Working.": "运行中。", "Working...": "运行中...",
    "Edited": "已编辑", "Viewed": "已查看", "Created": "已创建", "Deleted": "已删除", "Executed": "已执行",
    "Save rule to always allow write access to this path?": "保存规则以始终允许写入此路径吗？",
    "Save rule to always allow read access to this path?": "保存规则以始终允许读取此路径吗？",
    "Save rule to always allow execution of this command?": "保存规则以始终允许执行此命令吗？",
    "Yes, save rule in this conversation": "是，在本次对话中保存规则",
    "Yes, save rule when not in a project": "是，在未分组项目中保存规则",
    "Yes, save rule globally": "是，全局保存规则",

    // Error & Diagnostics UI
    "Our servers are experiencing high traffic right now, please try again in a minute.": "我们的服务器当前负载较高，请稍后重试。",
    "Error ID:": "错误 ID：",
    "Agent terminated due to error": "智能体因错误而终止",
    "Agent execution terminated due to error.": "智能体执行因错误而终止。",
    "Agent execution terminated due to error": "智能体执行因错误而终止",
    "You can prompt the model to try again or start a new conversation if the error persists.": "您可以提示模型重试，或者如果错误仍然存在，可以开启新的对话。",
    "See our troubleshooting guide for more help.": "查看我们的排查指南以获取更多帮助。",
    "See our troubleshooting guide for more help": "查看我们的排查指南以获取更多帮助",
    "troubleshooting guide": "排查指南", "troubleshooting_guide": "排查指南",
    "See our": "查看我们的",
    "for more help.": "以获取更多帮助。", "for more help": "以获取更多帮助",
    "Dismiss": "忽略", "Copy debug info": "复制调试信息",

    // Remote Control Feature & Prompts
    "Try Remote Control": "尝试远程控制",
    "Remote Control": "远程控制",
    "Kick off work on your computer and continue working with your agents from your phone or another device. Turn on Remote Control in app settings.": "在电脑上启动工作，并可以通过手机或其他设备继续与智能体协同工作。请在应用设置中开启“远程控制”。",
    "Kick off work on your computer and continue working with your agents from your phone or another device.": "在电脑上启动工作，并可以通过手机或其他设备继续与智能体协同工作。",
    "Turn on Remote Control in app settings.": "请在应用设置中开启“远程控制”。",
    "Turn on Remote Control in app settings": "请在应用设置中开启“远程控制”"
  ,
    // === Enhanced v2.27/v2.28 & Complete Localizations ===
    // --- Comprehensive Settings Translations ---
    // --- Screenshot 1 & 2 Specific Settings Translations ---
    "Manage your notification preferences.": "管理您的系统与声音通知偏好。",
    "Manage your notification preferences": "管理您的系统与声音通知偏好",
    "Enable Notifications for Agent": "启用智能体系统通知",
    "Show system notifications when your action is needed or the agent finishes.": "当需要您操作或智能体完成任务时显示系统通知。",
    "Show system notifications when your action is needed or the agent finishes": "当需要您操作或智能体完成任务时显示系统通知",
    "Sound": "声音提示",
    "Sounds": "声音提示",
    "Enable Sounds for Agent": "启用智能体提示音",
    "Play a sound when your action is needed or the agent finishes.": "当需要您操作或智能体完成任务时播放提示音。",
    "Play a sound when your action is needed or the agent finishes": "当需要您操作或智能体完成任务时播放提示音",
    "Volume": "音量",
    "Set the volume of agent sounds.": "调节智能体提示音的音量大小。",
    "Set the volume of agent sounds": "调节智能体提示音的音量大小",
    "Play test sound": "播放测试音",
    "Test sound": "测试声音",
    "Permissions": "权限管理",
    "Permission": "权限",
    "Configure what the agent can do in local and remote conversations.": "配置智能体在本地和远程对话中可以执行的操作。",
    "Configure what the agent can do in local and remote conversations": "配置智能体在本地和远程对话中可以执行的操作",
    "This Computer": "本机 (本地对话)",
    "this computer": "本机",
    "Remote": "远程对话",
    "remote": "远程",
    "Controls permissions for remote conversations.": "控制远程对话中的权限策略。",
    "Controls permissions for remote conversations": "控制远程对话中的权限策略",
    "Controls permissions for local conversations.": "控制本地对话中的权限策略。",
    "Controls permissions for local conversations": "控制本地对话中的权限策略",
    "Configure link opening and built-in browser preferences.": "配置链接打开方式以及内置浏览器偏好。",
    "Configure link opening and built-in browser preferences": "配置链接打开方式以及内置浏览器偏好",
    "Open Links In": "链接打开方式",
    "Open links in": "链接打开方式",
    "External Browser": "外部默认浏览器",
    "external browser": "外部默认浏览器",
    "built-in browser": "内置浏览器",
    "Give Feedback": "意见反馈",
    "Give feedback": "意见反馈",
    "Manage Account": "管理账户",
    "Manage account": "管理账户",
    "General Settings": "常规设置",
    "General Preferences": "常规偏好",
    "Account & Plan": "账户与方案",
    "Billing & Usage": "账单与使用量",
    "Billing & Quota": "账单与额度",
    "Model Configuration": "模型配置",
    "Model Parameters": "模型参数",
    "Customizations & Plugins": "定制项与插件",
    "Plugins & Extensions": "插件与扩展",
    "Web Automation": "网页自动化",
    "System & Tray": "系统与托盘",
    "Conversations & Permissions": "对话与权限",
    "Agent Permissions": "智能体权限",
    "Security & Sandboxing": "安全与沙箱",
    "Terminal Sandbox": "终端沙箱隔离",
    "Error & Diagnostics": "错误与诊断",
    "Logs & Telemetry": "日志与遥测",
    "Device Pairing": "设备配对",
    "Keybindings Reference": "快捷键参考",
    "Legal & Terms": "法律与条款",
    "Security & Permissions": "安全与权限",
    "Tool Access & Automation": "工具访问与自动化",
    "Command Auto-Execution": "命令自动执行",
    "File System Access": "文件系统访问",
    "Network Access": "网络访问",
    "Terminal Execution": "终端执行",
    "Agent Behavior & Autonomy": "智能体行为与自主度",
    "Context & Memory": "上下文与记忆",
    "Display & Appearance": "显示与外观",
    "Updates & Diagnostics": "更新与诊断",
    "Permission Preset": "权限预设方案",
    "Permission Presets": "权限预设方案",
    "Security Presets": "安全预设方案",
    "Predefined security presets": "预定义安全预设方案",
    "Turbo Mode": "极速模式",
    "Balanced Mode": "均衡模式",
    "Balanced mode": "均衡模式",
    "Strict": "严格模式",
    "Strict Mode": "严格模式",
    "Paranoid": "极端审阅模式",
    "Paranoid Mode": "极端审阅模式",
    "Paranoid mode": "极端审阅模式",
    "Custom Preset": "自定义预设",
    "Eager": "立即执行",
    "EAGER": "立即执行",
    "Ask First": "每次询问",
    "Require Approval": "需要审批确认",
    "Auto-Execution Policy": "自动执行策略",
    "Command Auto-Execution Policy": "命令自动执行策略",
    "Auto-run all permitted commands": "自动运行所有受信任命令",
    "Prompt for approval before running commands": "运行命令前提示审批确认",
    "Non-Workspace File Access Policy": "工作区外部文件访问策略",
    "File Access Policy": "文件访问策略",
    "Access outside workspace": "访问工作区外部",
    "Allow reading and editing files outside the project workspace": "允许读取和编辑工作区外部的文件",
    "Prompt for approval when accessing files outside the project workspace": "访问工作区外部文件时弹窗询问",
    "Block access to any files outside the project workspace": "禁止访问任何工作区外部的文件",
    "Artifact Review Mode": "产物审阅模式",
    "Require user confirmation before proceeding with artifact steps": "在产物分步执行前需要用户确认",
    "Auto-approve artifact actions": "自动批准产物操作",
    "Enable Terminal Sandbox": "启用终端沙箱隔离",
    "Runs terminal commands in a restricted Windows container or isolated sandbox environment.": "在受限的 Windows 容器或受控沙箱环境中运行终端命令。",
    "Runs terminal commands in a restricted sandbox environment.": "在受限的沙箱隔离环境中运行终端命令。",
    "Runs bash and terminal commands in a restricted Windows container or WSL environment.": "在受限的 Windows 容器或 WSL 环境中运行终端命令。",
    "Sandbox is currently disabled.": "沙箱当前已禁用。",
    "Sandbox is currently enabled.": "沙箱当前已启用。",
    "Set up sandboxing": "配置沙箱环境",
    "Administrator privileges are required to set up sandboxing.": "配置沙箱环境需要 Windows 管理员权限。",
    "Learn more about sandboxing": "了解关于沙箱的更多信息",
    "Sandboxing requires WSL or Windows Hyper-V.": "沙箱功能需要 WSL 或 Windows Hyper-V 支持。",
    "Always ask": "每次询问",
    "Always proceed": "始终执行",
    "Never Allow": "从不允许",
    "Never allow": "从不允许",
    "Require approval": "需要审批确认",
    "Inherit global": "继承全局设置",
    "Custom Rules": "自定义规则",
    "Reset to Defaults": "恢复默认值",
    "Save Settings": "保存设置",
    "Apply Changes": "应用更改",
    "Discard Changes": "放弃更改",
    "Prevent computer sleep": "防止计算机休眠",
    "Automatically check for updates": "自动检查更新",
    "Download updates automatically": "自动下载更新",
    "Enable telemetry": "启用匿名遥测",
    "Allow anonymous crash reports and telemetry": "允许发送匿名崩溃报告与使用遥测以帮助优化软件",
    "Google Account": "Google 账户",
    "Switch Account": "切换账户",
    "Sign in to access models and features": "登录以访问高级模型与完整功能",
    "Subscription & Billing": "订阅与账单",
    "Manage Plan": "管理方案",
    "Active Subscription": "当前订阅有效",
    "Renews on": "续费日期：",
    "Expires on": "到期日期：",
    "Payment Method": "支付方式",
    "Billing Period": "计费周期",
    "Model Quota": "模型请求额度",
    "Available AI Credits": "可用 AI 积分",
    "When toggled on, Antigravity will use your AI credits to fulfill model requests once you're out of model quota.": "开启后，当模型免费额度用尽时，Antigravity 将自动使用您的 AI 积分继续处理请求。",
    "Buy AI Credits": "购买 AI 积分",
    "Monthly Limit Remaining": "每月限额剩余",
    "5-Hour Limit Remaining": "五小时限额剩余",
    "Resets in": "重置倒计时：",
    "Allow controlling this instance of Antigravity from other devices.": "允许从其他设备或移动端远程控制当前的 Antigravity 实例。",
    "Allow controlling this instance of Antigravity from other devices or mobile app.": "允许从其他设备或移动应用远程连接并控制当前 Antigravity 实例。",
    "Device Name": "设备名称",
    "Pairing Code": "配对码",
    "Generate New Code": "生成新配对码",
    "Status: Connected": "状态：已连接",
    "Status: Disconnected": "状态：未连接",
    "Status: Listening": "状态：等待连接中",
    "View logs and diagnostic information for troubleshooting.": "查看日志与诊断信息以排查故障与异常。",
    "Export Diagnostics": "导出诊断报告",
    "Copy Diagnostics to Clipboard": "复制诊断信息到剪贴板",
    "Open Logs Folder": "打开日志存储文件夹",
    "Clear Logs": "清空日志记录",
    "Electron Logs": "Electron 客户端主日志",
    "Language Server Logs": "语言服务 (Language Server) 日志",
    "Preferred Model": "首选模型",
    "Customize default system instructions for the agent.": "为智能体配置默认的系统级全局前置提示词指令。",
    "Default Behaviors, Skills, and MCP Servers": "默认行为规范、技能与 MCP 服务器",
    "Token Usage Breakdown": "Token 预算与使用明细",
    "The breakdown below shows token usage from customizations like rules, skills, and MCP.": "下方展示了提示词规则、技能与 MCP 工具等定制项的 Token 消耗明细。",
    "If a budget is exceeded, large rules are demoted to path pointers and large customizations are excluded automatically.": "当超出上下文预算时，大型规则会自动降级为文件路径指针，大型定制项将被自动排除以保证对话性能。",
    "Available Budget": "可用 Token 预算",
    "Add Custom MCP Server": "添加自定义 MCP 服务器",
    "Configure MCP Server": "配置 MCP 服务器",
    "Environment Variables": "环境变量",
    "Arguments": "运行参数",
    "Server Name": "服务器名称",
    "Reading file...": "正在读取文件...",
    "Writing file...": "正在写入文件...",
    "Editing file...": "正在编辑文件...",
    "Running command...": "正在运行命令...",
    "Ran command...": "已运行命令...",
    "Read file...": "已读取文件...",
    "Wrote file...": "已写入文件...",
    "Edited file...": "已编辑文件...",
    "Searching web...": "正在搜索网络...",
    "Searched web...": "已搜索网络...",
    "Listing directory...": "正在列出目录...",
    "Listed directory...": "已列出目录...",
    "Tool is running as a background task": "工具正在后台任务中运行",
    "Task logs are available at:": "任务日志位于:",
    "Command output:": "命令输出:",
    "No output from the command.": "命令无输出。",
    "Tool execution was canceled": "工具执行已取消",
    "Command exited with code 0.": "命令已退出，返回码 0。",
    "Command exited with code 1.": "命令已退出，返回码 1。",
    "Command exited with code": "命令退出代码",
    "Created file.": "文件创建成功。",
    "Created file": "创建文件",
    "Made 1 replacement in": "完成 1 处替换于",
    "Encountered error in tool execution:": "工具执行时遇到错误:",
    "Do you want to run this command?": "您确定要运行此命令吗？",
    "Do you want to edit this file?": "您确定要编辑此文件吗？",
    "Do you want to create this file?": "您确定要创建此文件吗？",
    "Do you want to delete this file?": "您确定要删除此文件吗？",
    "Approve": "批准",
    "Always allow": "始终允许",
    "Allow once": "仅允许本次",
    "Always Allow": "始终允许",
    "Allow Once": "仅允许本次",
    "Reject": "拒绝",
    "Proceed": "继续",
    "Proceed to execute": "继续执行",
    "Show diff": "显示差异",
    "Hide diff": "隐藏差异",
    "Expand": "展开",
    "Collapse": "折叠",
    "Revert": "还原",
    "Accept": "接受",
    "View diff": "查看差异",
    "Apply changes": "应用更改",
    "Discard changes": "放弃更改",
    "Discard All": "全部放弃",
    "Details": "详情",
    "Jump to": "跳转至",
    "Past 30 days": "过去 30 天",
    "All Time": "所有时间",
    "Ask anything...": "输入任何问题...",
    "Type / for actions, @ to mention": "输入 / 执行操作，使用 @ 提及",
    "Stop generating": "停止生成",
    "Stop Generation": "停止生成",
    "Quality": "高质量模式",
    "Thought for": "思考耗时",
    "Worked for": "运行耗时",
    "Record audio": "录制音频",
    "Stop recording": "停止录音",
    "Transcribing...": "正在转写语音...",
    "Send feedback": "发送反馈",
    "Provide feedback": "提供反馈",
    "Commands": "命令",
    "Run a long-running task": "执行长周期任务直到达成目标",
    "Compact conversation context": "压缩对话上下文以节省空间",
    "Schedule a recurring or one-time timer": "设置单次计时器或周期性定时任务",
    "Web browsing and interacting with web applications": "浏览网页并与网络应用交互",
    "Step-by-step planning before execution": "执行复杂任务前的分步规划方案",
    "Interactive interview to resolve design decisions": "通过交互式问答明确方案设计",
    "Team of autonomous agents working together": "多智能体协同协作处理大型项目",
    "Persist behavior for future tasks": "记忆此行为以用于后续任务",
    "Complex coding or research project": "深度思考与严谨验证的高难度任务",
    "Design and create automated scheduled tasks": "设计并创建后台自动化定时任务",
    "Manage and create plugins": "管理与创建插件生态包",
    "Symbols": "代码符号",
    "Web": "网络搜索",
    "Git": "Git 版本控制",
    "Search files...": "搜索文件...",
    "Search symbols...": "搜索代码符号...",
    "No active goals": "暂无进行中的目标",
    "No active tasks": "暂无进行中的任务",
    "No goals": "暂无目标",
    "No tasks": "暂无任务",
    "Next steps": "下一步行动",
    "Next Steps": "下一步行动",
    "Summary": "概要",
    "Changes to review": "待审阅更改",
    "No changes to review": "暂无待审阅更改",
    "Side by side": "并排对比",
    "Open file": "打开文件",
    "Reveal in Explorer": "在文件资源管理器中显示",
    "Reveal in Finder": "在访达中显示",
    "New File": "新建文件",
    "New Folder": "新建文件夹",
    "Kill Terminal": "关闭终端",
    "Clear Terminal": "清空终端",
    "Terminal 1": "终端 1",
    "Design, Creative & Media": "设计、创意与媒体",
    "Productivity & Project Management": "生产力与项目管理",
    "Cloud Hosting & Deployment": "云端托管与部署",
    "Business": "商业与企业服务",
    "More Plugins": "更多插件",
    "Install": "安装",
    "Uninstall": "卸载",
    "Configure": "配置",
    "Author": "作者",
    "Capabilities": "扩展能力",
    "Hooks": "生命周期钩子",
    "Search Marketplace": "搜索插件市场",
    "Open in External Browser": "在外部浏览器中打开",
    "Actual Size": "实际大小",
    "Print": "打印",
    "Page": "页",
    "Security": "安全性",
    "Customization": "定制项",
    "Open Project": "打开项目",
    "Rename Project": "重命名项目",
    "Delete Project": "删除项目",
    "Project Settings": "项目设置",
    "outside-of-project": "未分组对话",
    "outside of project": "未分组对话",
    "Untitled Conversation": "未命名对话",
    "Unpin": "取消置顶",
    "Checking for Updates...": "正在检查更新...",
    "Check for updates": "检查更新",
    "Checking for updates...": "正在检查更新...",
    "Update Available": "有可用更新",
    "Downloading Update...": "正在下载更新...",
    "Restart to Update": "重启以应用更新",
    "You're on the latest version": "您当前使用的是最新版本",
    "You are on the latest version": "您当前使用的是最新版本",
    "No updates available": "暂无可用更新",
    "About Antigravity": "关于 Antigravity",
    "Logged in as": "当前登录身份",
    "Sign in": "登录",
    "Sign In": "登录",
    "Sign out": "退出登录",
    "Manage Subscription": "管理订阅",
    "Pro Plan": "Pro 方案",
    "Ultra Plan": "Ultra 方案",
    "Free Plan": "免费方案",
    "AI Credits": "AI 积分",
    "Token budget": "Token 预算",
    "Customization Budget": "定制项 Token 预算",
    "Keep in Menu Bar": "保留在系统托盘/菜单栏",
    "Release Notes": "发行说明",
    "Gemini 4 Argon (High)": "Gemini 4 Argon (高思考)",
    "Gemini 4 Argon (Low)": "Gemini 4 Argon (低思考)",
    "Gemini 4 Argon High": "Gemini 4 Argon (高思考)",
    "Gemini 4 Argon Low": "Gemini 4 Argon (低思考)",
    "Sonnet 5.5": "Sonnet 5.5",
    "Thinking Budget": "思考预算",
    "Context Window": "上下文窗口",
    "Add Files": "添加文件",
    "Add Folder": "添加文件夹",
    "Add Screenshot": "添加屏幕截图",
    "File": "文件",
    "View": "视图",
    "Show Antigravity": "显示 Antigravity",
    "Quit": "退出",
    "Quit Antigravity": "退出 Antigravity",
    "Conversation Navigator": "对话导航器",
    "Conversation navigator": "对话导航器",
    "Navigator": "导航器",
    "Jump to turn": "跳转至对话轮次",
    "Jump to Turn": "跳转至对话轮次",
    "Turn": "轮次",
    "Turns": "轮次",
    "Chapters": "章节",
    "Chapter": "章节",
    "Earlier today": "今天更早",
    "Past 7 days": "过去 7 天",
    "This week": "本周",
    "This month": "本月",
    "Last month": "上月",
    "Navigate conversation": "导航对话",
    "Notification Preferences": "通知偏好设置",
    "Notification preferences": "通知偏好设置",
    "Notification Preference": "通知偏好设置",
    "Choose whether to be notified when the agent needs your attention or completes a task.": "选择当智能体需要您的关注或完成任务时是否接收通知。",
    "Choose whether to be notified when the agent needs your attention or completes a task": "选择当智能体需要您的关注或完成任务时是否接收通知",
    "Open Preferences": "打开偏好设置",
    "Open preferences": "打开偏好设置",
    "Preferences": "偏好设置",
    "Dismiss": "忽略",
    "dismiss": "忽略",
    "Don't ask again": "不再询问",
    "Don't Ask Again": "不再询问",
    "Gemini 4 Argon": "Gemini 4 Argon",
    "Gemini 4 Argon is now available to paid Pro plan subscribers.": "Gemini 4 Argon 现已面向付费 Pro 计划订阅用户开放。",
    "Gemini 4 Argon is now available to paid Pro plan subscribers": "Gemini 4 Argon 现已面向付费 Pro 计划订阅用户开放",
    "paid Pro plan subscribers": "付费 Pro 计划订阅用户",
    "paid Pro plan": "付费 Pro 计划",
    "paid Pro and Ultra plans": "付费 Pro 和 Ultra 计划",
    "Pro plan": "Pro 计划",
    "Ultra plan": "Ultra 计划",
    "Free plan": "免费计划",
    "Upgrade to Pro": "升级到 Pro",
    "Upgrade to Ultra": "升级到 Ultra",
    "Upgrade plan": "升级方案",
    "Upgrade Plan": "升级方案",
    "Built-in Browser": "内置浏览器",
    "Built-in browser": "内置浏览器",
    "Browser": "浏览器",
    "Open in Browser": "在浏览器中打开",
    "Open in browser": "在浏览器中打开",
    "Open in New Tab": "在新标签页中打开",
    "Open in new tab": "在新标签页中打开",
    "Open link in new tab": "在新标签页中打开链接",
    "Reopen Closed Tab": "重新打开已关闭标签页",
    "Reopen closed tab": "重新打开已关闭标签页",
    "Reload Tab": "重新加载标签页",
    "Reload tab": "重新加载标签页",
    "Close Tab": "关闭标签页",
    "Close tab": "关闭标签页",
    "Close Other Tabs": "关闭其他标签页",
    "Close other tabs": "关闭其他标签页",
    "Close Tabs to the Right": "关闭右侧标签页",
    "Close tabs to the right": "关闭右侧标签页",
    "Duplicate Tab": "复制标签页",
    "Duplicate tab": "复制标签页",
    "PDF Viewer": "PDF 阅读器",
    "Fit to Page": "适应页面",
    "Fit to Width": "适应宽度",
    "Fit to page": "适应页面",
    "Fit to width": "适应宽度",
    "Rotate Clockwise": "顺时针旋转",
    "Rotate Counterclockwise": "逆时针旋转",
    "Secure Connection": "安全连接",
    "Not Secure": "不安全",
    "Certificate": "证书",
    "Certificate Viewer": "证书查看器",
    "Connection is secure": "连接安全",
    "Connection is not secure": "连接不安全",
    "Marketplace": "插件市场",
    "Featured": "精选推荐",
    "Featured Plugins": "精选插件",
    "All Plugins": "全部插件",
    "Installed Plugins": "已安装插件",
    "Installed": "已安装",
    "Verified Publisher": "官方认证发布者",
    "Official": "官方",
    "Partner": "合作伙伴",
    "Community": "社区",
    "Developer": "开发者",
    "Website": "官方网站",
    "Repository": "代码仓库",
    "Privacy Policy": "隐私政策",
    "Google's Privacy Policy": "Google 隐私政策",
    "Third-party developer": "第三方开发者",
    "Third-party developer transparency notice": "第三方开发者透明度说明",
    "This plugin is provided by a third-party developer.": "此插件由第三方开发者提供。",
    "Install Plugin": "安装插件",
    "Install plugin": "安装插件",
    "Installing...": "正在安装...",
    "Uninstall Plugin": "卸载插件",
    "Uninstall plugin": "卸载插件",
    "Uninstalling...": "正在卸载...",
    "Manage Plugins": "管理插件",
    "Manage plugins": "管理插件",
    "Search plugins...": "搜索插件...",
    "Search plugins": "搜索插件",
    "No plugins found": "未找到相关插件",
    "No plugins found.": "未找到相关插件。",
    "Add Plugin": "添加插件",
    "Browse Marketplace": "浏览插件市场",
    "Recommended": "推荐",
    "Attach Files": "添加附件",
    "Attach files": "添加附件",
    "Attach File": "添加附件",
    "Attach file": "添加附件",
    "Attach Folder": "添加文件夹",
    "Attach folder": "添加文件夹",
    "Drag and drop files here": "拖拽文件至此处",
    "Drag & drop files here": "拖拽文件至此处",
    "Drop files here": "放置文件至此处",
    "Drop files to attach": "放置文件以作为附件",
    "Upload complete": "上传完成",
    "Uploading...": "正在上传...",
    "Failed to upload": "上传失败",
    "File size exceeds limit": "文件大小超出限制",
    "Unsupported file type": "不支持的文件类型",
    "Maximum file size": "最大文件大小",
    "All Files": "所有文件",
    "Word Diff": "逐词对比",
    "Word diff": "逐词对比",
    "Character Diff": "逐字对比",
    "Character diff": "逐字对比",
    "Inline Diff": "内联对比",
    "Inline diff": "内联对比",
    "Side-by-side": "并排对比",
    "Side-by-side diff": "并排对比",
    "Side by Side": "并排对比",
    "Accept All": "全部接受",
    "Accept all": "全部接受",
    "Reject All": "全部拒绝",
    "Reject all": "全部拒绝",
    "Accept Change": "接受更改",
    "Accept change": "接受更改",
    "Reject Change": "拒绝更改",
    "Reject change": "拒绝更改",
    "Review changes": "审阅更改",
    "Review Changes": "审阅更改",
    "Previous Change": "上一个更改",
    "Previous change": "上一个更改",
    "Next Change": "下一个更改",
    "Next change": "下一个更改",
    "Previous Difference": "上一个差异",
    "Previous difference": "上一个差异",
    "Next Difference": "下一个差异",
    "Next difference": "下一个差异",
    "Unsaved changes": "未保存的更改",
    "Modified files": "已修改的文件",
    "Revert change": "还原更改",
    "Revert all": "全部还原",
    "Discard change": "放弃更改",
    "Discard all": "全部放弃",
    "Gemini 3.8 Flash (High)": "Gemini 3.8 Flash (高思考)",
    "Gemini 3.8 Flash (Low)": "Gemini 3.8 Flash (低思考)",
    "Gemini 3.8 Flash High": "Gemini 3.8 Flash (高思考)",
    "Gemini 3.8 Flash Low": "Gemini 3.8 Flash (低思考)",
    "Gemini 3.8 Flash": "Gemini 3.8 Flash",
    "Gemini 3 Pro": "Gemini 3 Pro",
    "Claude 3.7 Sonnet": "Claude 3.7 Sonnet",
    "Claude 3.5 Sonnet": "Claude 3.5 Sonnet",
    "Reasoning Effort": "思考推理强度",
    "Reasoning effort": "思考推理强度",
    "Thinking": "思考过程",
    "Turbo": "极速模式",
    "Balanced": "均衡模式",
    "High": "高",
    "Medium": "中",
    "Low": "低",
    "Default": "默认",
    "Experimental": "实验性",
    "Context window": "上下文窗口",
    "Temperature": "温度参数",
    "Top P": "采样 Top P",
    "Max Tokens": "最大 Token 数",
    "Ask anything, @ to mention, / for actions": "输入任何问题，使用 @ 提及，使用 / 执行操作",
    "Ask anything, @ to mention": "输入任何问题，使用 @ 提及",
    "Ask anything": "输入任何问题",
    "Type / for actions": "输入 / 执行操作",
    "Type @ to mention": "输入 @ 提及",
    "Slash Commands": "快捷斜杠命令",
    "Slash commands": "快捷斜杠命令",
    "Quick actions": "快捷操作",
    "Quick Actions": "快捷操作",
    "Insert at cursor": "插入光标处",
    "Copy code": "复制代码",
    "Code copied": "代码已复制",
    "Copied!": "已复制！",
    "Copy to clipboard": "复制到剪贴板",
    "Add context": "添加上下文",
    "Add Context": "添加上下文",
    "Thinking...": "思考中...",
    "Working...": "运行中...",
    "Open IDE": "打开 IDE",
    "Open in IDE": "在 IDE 中打开",
    "Open External": "在外部打开",
    "Auxiliary Pane": "辅助面板",
    "Toggle Auxiliary Pane": "切换辅助面板",
    "Setting up WSL": "正在配置 WSL",
    "Connect to WSL": "连接至 WSL",
    "Reopen Locally": "在本地重新打开",
    "Docs": "官方文档",
    "Documentation": "官方文档",
    "Help": "帮助",
    "Feedback": "意见反馈",
    "Report an Issue": "报告问题",
    "Keyboard Shortcuts": "键盘快捷键",
    "Shortcuts": "快捷键",
    "Scratchpad": "便签草稿",
    "Overview": "概览",
    "Review": "审阅",
    "Files": "文件",
    "Terminal": "终端",
    "Plugins": "插件",
    "Uploads": "已上传文件",
    "Background Tasks": "后台任务",
    "Automations": "自动化",
    "Customizations": "定制项",
    "Projects": "项目",
    "New Project": "新建项目",
    "Create Project": "创建项目"
};

  const coreWords = {
    "create": "创建", "delete": "删除", "new": "新建", "edit": "编辑", "save": "保存", "cancel": "取消", "confirm": "确认",
    "close": "关闭", "open": "打开", "stop": "停止", "start": "启动", "run": "运行", "add": "添加", "remove": "移除", "download": "下载",
    "update": "更新", "select": "选择", "clear": "清除", "search": "搜索", "find": "查找", "view": "查看", "show": "显示", "hide": "隐藏",
    "copy": "复制", "paste": "粘贴", "cut": "剪切", "rename": "重命名", "duplicate": "制作副本",
    "agent": "智能体", "agents": "智能体", "subagent": "子智能体", "subagents": "子智能体", "task": "任务", "tasks": "任务",
    "workspace": "工作区", "workspaces": "工作区", "directory": "目录", "folder": "文件夹", "file": "文件", "files": "文件",
    "command": "命令", "commands": "命令", "terminal": "终端", "console": "控制台", "output": "输出", "input": "输入",
    "error": "错误", "warning": "警告", "info": "信息", "success": "成功", "failed": "失败", "pending": "等待中", "running": "运行中",
    "yes": "是", "no": "否", "true": "真", "false": "假", "on": "开", "off": "关", "enable": "启用", "disable": "禁用",
    "global": "全局", "retry": "重试", "regenerate": "重新生成", "dismiss": "忽略",
    "allow": "允许", "ask": "询问", "deny": "拒绝", "split": "分屏", "notice": "提示"
  };

  // Structured Prefix & Content Match Rules for Complex / Truncated Text
  const textPrefixRules = [
    // --- Screenshot Prefix Rules ---
    ["Manage your notification preferences", "管理您的系统与声音通知偏好。"],
    ["Show system notifications when your action is needed", "当需要您操作或智能体完成任务时显示系统通知。"],
    ["Play a sound when your action is needed", "当需要您操作或智能体完成任务时播放提示音。"],
    ["Set the volume of agent sounds", "调节智能体提示音的音量大小。"],
    ["Configure what the agent can do in local and remote conversations", "配置智能体在本地和远程对话中可以执行的操作。"],
    ["Controls permissions for remote conversations", "控制远程对话中的权限策略。"],
    ["Controls permissions for local conversations", "控制本地对话中的权限策略。"],
    ["Configure link opening and built-in browser preferences", "配置链接打开方式以及内置浏览器偏好。"],
    // --- Settings Prefix Rules ---
    ["Choose a predefined security preset", "为智能体选择预设的安全策略方案。这控制着终端自动执行策略与文件访问权限。"],
    ["Useful for typical development with an emphasis on security", "适用于注重安全性的常规开发场景。它优先保证安全性，对所有终端命令和项目目录外的文件访问都需要手动批准。"],
    ["All terminal commands require review", "所有终端命令均需人工审阅。智能体可以读取或写入系统中的任何文件。"],
    ["Disables all safety barriers", "禁用所有安全限制屏障，以换取最高的自动化迭代速度。"],
    ["Prioritizes safety over speed", "优先保证安全性，对所有终端命令和项目目录外的文件访问都需要手动批准。"],
    ["Prioritizes velocity", "优先追求自动化速度。所有命令和文件操作均全自动执行，无需弹窗确认。"],
    ["Balances speed and safety", "平衡执行速度与安全性。高风险命令与工作区外部文件修改需要审阅确认。"],
    ["Runs terminal commands in a restricted", "在受限的容器或受控沙箱隔离环境中运行终端命令。"],
    ["Runs bash and terminal commands in a restricted", "在受限的 Windows 容器或 WSL 环境中运行终端命令。"],
    ["When toggled on, Antigravity will use your AI credits", "开启后，当模型免费额度用尽时，Antigravity 将自动使用您的 AI 积分继续处理请求。"],
    ["When toggled on, Antigravity collects usage data", "开启后，Antigravity 将收集匿名使用数据以帮助 Google 持续优化性能和功能。"],
    ["Receive product updates, tips, and promotions", "通过电子邮件接收来自 Google Antigravity 的产品更新、技巧与动态。"],
    ["You can upgrade to a Google AI Ultra plan", "您可以升级至 Google AI Ultra 方案以获得更高的请求限额。"],
    ["Controls whether the agent can automatically execute", "控制智能体是否可以全自动执行终端命令。"],
    ["Controls whether the agent can read and edit files outside", "控制智能体是否可以读取或编辑当前项目工作区文件夹外部的文件。"],
    ["Controls whether the agent can run custom JavaScript", "控制智能体是否可以运行自定义 JavaScript 来自动化复杂的浏览器操作。"],
    ["Specifies Agent\'s behavior when asking for review on artifacts", "指定智能体在创建产物（如设计文档、规划方案等）时是否向您请求审阅确认。"],
    ["The app will be accessible from the menu bar", "所有窗口关闭后，应用程序依然常驻在系统托盘并在后台保持运行。"],
    ["Keep the app accessible from the menu bar", "所有窗口关闭后，应用程序依然常驻在系统托盘并在后台保持运行。"],
    ["Prevent the computer from sleeping while the app is running", "在应用程序运行及长周期任务执行时，防止计算机进入休眠状态。"],
    ["To modify notification settings, open your operating system", "如需更改通知显示方式，请打开操作系统的系统偏好设置。"],
    ["View logs and diagnostic information for troubleshooting", "查看日志与诊断信息以排查故障与异常。"],
    ["Allow controlling this instance of Antigravity from other devices", "允许从其他设备或移动端远程控制当前的 Antigravity 实例。"],
    ["If a budget is exceeded, large rules are demoted", "当超出上下文预算时，大型规则会自动降级为文件路径指针，大型定制项将被自动排除以保证对话性能。"],
    ["The breakdown below shows token usage", "下方明细展示了规则、技能与 MCP 等定制项的 Token 消耗情况。"],
    ["Allow/deny agent command execution outside the sandbox", "允许或拒绝智能体在沙箱外部直接执行命令。"],
    ["Allow/deny agent read access to specific files", "允许或拒绝智能体读取特定文件或目录。"],
    ["Allow/deny agent write access to specific files", "允许或拒绝智能体写入或修改特定文件或目录。"],
    ["Allow/deny agent browser actuation access to specific URLs", "允许或拒绝智能体在特定网页 URL 上进行浏览器自动化交互。"],

    // Plugins & Customizations
    ["Plugins are packaged collections of skills and MCPs to help the Agent in", "插件是技能和 MCP 的打包集合，用于帮助 "],
    ["Plugins are packaged collections of skills and MCPs", "插件是技能和 MCP 的打包集合，用于帮助 "],
    ["work with Google developer products. You can always change your choices in Settings.", " 中的智能体与 Google 开发者产品协同工作。您可以随时在“设置”中更改您的选择。"],
    ["Provides a comprehensive guide", "提供 Google Antigravity (AGY) 的综合指南、快速参考和站点地图，包括 Antigravity CLI、Antigravity 2.0、IDE、Python SDK、斜杠命令、快捷键和自定义项。"],
    ["How to render rich interactive HTML widgets inline in the chat or as standalone artifacts. Use this skill", "如何在对话中内联或作为独立产物渲染丰富的交互式 HTML 小部件。当您想要向用户显示图表、数据可视化或交互式控件时，请使用此技能。"],
    ["Automatically migrate legacy workflows", "自动将旧版工作流迁移到技能目录。它会扫描现有工作流，并创建目标..."],
    ["Guidelines for interacting with GitHub and request permissions", "关于与 GitHub 交互的指南，并在智能体环境中由于限制导致命令失败时向用户请求相应的权限。"],
    ["Comprehensive guide and reference for the Antigravity Customization System", "Antigravity 自定义系统的综合指南和参考。用于解释自定义项的工作原理、加载优先级、发现机制，并指导创建技能、规则、插件、钩子和 MCP 服务器。"],
    ["Skills providing tailored instructions for happy path", "提供 Dart 和 Flutter 开发主流程定制化指南的技能。"],
    ["Interactive guide to design and create a scheduled background automation", "设计和创建计划后台自动化的交互式指南。当用户想要创建自动化或周期性计划任务时（例如“总结我的邮件”），请使用此技能。"],
    ["How to manage and create plugins", "如何管理和创建插件——作为单一单元安装、启用和禁用的命名空间技能、智能体、规则、MCP 服务器和钩子捆绑包。"],
    ["Build, package, run, and debug UI extensions for Antigravity", "为 Antigravity 构建、打包、运行和调试 UI 扩展：在侧边面板中渲染的交互式 Web 面板，由使用内置 Sidecar SDK 的 Node.js sidecar 提供服务。"],
    ["Discover UI plugin panels relevant to the current task", "发现与当前任务相关的 UI 插件面板，并在对话中显示一键式快捷胶囊以在侧边面板中打开（切换）它们。"],
    ["Build and prototype location-aware applications with Google Maps Platform", "使用 Google Maps Platform 构建具有位置感知能力的应用并设计原型。"],
    ["Specialized suite of skills for data engineers and database", "专为 Google Cloud 上的数据工程师和数据库从业人员打造的专业技能套件。"],
    ["Build applications with the Gemini Interactions API and Live API", "使用 Gemini Interactions API 和 Live API 构建应用，包括文本生成、多轮对话等功能。"],
    ["Build on Google's developer platforms, including Android, Chrome, Gemini, and Google Cloud.", "基于 Google 开发者平台（包括 Android、Chrome、Gemini 和 Google Cloud）构建。"],
    ["Prototype, build & run modern apps that user", "原型设计、构建和运行现代应用程序..."],
    ["Curated collection of agent skills for science t", "为科学任务精心挑选的智能体技能集合。"],
    ["Using the Google Antigravity Python SDK to b", "使用 Google Antigravity Python SDK 构建自定义智能体..."],
    ["Search and retrieve official documentation acr", "搜索和检索官方开发者文档..."],
    ["Integration skill and tools for Google Maps Pl", "适用于 Google Maps Platform 的集成技能和工具。"],
    ["Official plugin for Dart and Flutter that installs", "Dart 和 Flutter 官方插件，提供相关工具安装和开发支持。"],
    ["This plugin provides a specialized suite of skill", "此插件提供一套专为数据处理打造的专业技能..."],
    ["Connect to Google Workspace, including Docs, Sheets, Slides, Drive, and Calendar.", "连接到 Google Workspace，包括文档、表格、幻灯片、云端硬盘和日历。"],
    ["Read, draft, and edit docs.", "读取、起草和编辑文档。"],
    ["Read, write, and format spreadsheets.", "读取、写入和格式化电子表格。"],
    ["Read, edit, and export presentations.", "读取、编辑和导出演示文稿。"],
    ["Search, upload, download, and share files.", "搜索、上传、下载和共享文件。"],
    ["Check availability, schedule events, and RSVP.", "查看空闲时间、安排活动并回复邀请。"],

    // MCP Servers Descriptions
    ["Investigate and fix software issues using AI-powered root cause analysis", "使用 AI 驱动的根本原因分析来调查和修复软件问题。此 MCP 服务器连接到您的 Antimetal 账户..."],
    ["Query and act on your marketing, analytics, CRM, e-commerce", "跨 325 多个连接器查询并处理您的营销、分析、CRM、电子商务和仓库数据..."],
    ["Query your GitLab SDLC as a knowledge graph", "将您的 GitLab SDLC 作为知识图谱进行查询。Orbit 会建立相关索引..."],
    ["Enable Antigravity to deploy apps to Google Cloud Run", "使 Antigravity 能够将应用部署到 Google Cloud Run。"],
    ["Search and reference over 600,000 real-world app screens", "搜索并参考超过 600,000 个真实的应用程序屏幕、用户流程和 UI 模式..."],
    ["Build, edit, deploy, and manage full-stack web apps with Lovable", "使用自然语言，通过 Lovable 构建、编辑、部署和管理全栈 Web 应用..."],
    ["The GKE remote MCP server provides read write access to your GKE", "GKE 远程 MCP 服务器提供对您的 GKE Kubernetes 资源的读写访问权限。"],
    ["The Dart and Flutter MCP server exposes Dart (and Flutter)", "Dart 和 Flutter MCP 服务器向兼容的 AI 助手客户端公开相关开发工具操作。"],
    ["The Firebase Model Context Protocol (MCP) Server gives AI-powered", "Firebase MCP 服务器使 AI 工具能够处理您的 Firebase 项目和应用程序代码库。"],
    ["The Genkit Model Context Protocol (MCP) Server gives AI-powered", "Genkit MCP 服务器使 AI 工具能够构建、调试和检查您的 Genkit 应用。"],
    ["The gopls Model Context Protocol (MCP) server provides tools", "gopls MCP 服务器为您的 Go 代码库提供语义代码分析、实时诊断和转换工具。"],
    ["Interact with your BigQuery data using natural language", "使用自然语言与您的 BigQuery 数据交互。允许您安全地连接到您的数据集..."],
    ["The AlloyDB for PostgreSQL remote MCP server lets you access", "AlloyDB for PostgreSQL 远程 MCP 服务器允许您访问和运行 AlloyDB 工具..."],
    ["The Bigtable Admin remote MCP server lets you manage Bigtable", "Bigtable Admin 远程 MCP 服务器允许您管理 Bigtable 资源。"],
    ["The Cloud SQL remote MCP server lets you access and run Cloud SQL", "Cloud SQL 远程 MCP 服务器允许您访问和运行 Cloud SQL 工具..."],
    ["The Spanner remote MCP server lets you access and run Spanner", "Spanner 远程 MCP 服务器允许您访问和运行 Spanner 工具..."],
    ["The Apigee API hub remote MCP server lets you manage", "Apigee API hub 远程 MCP 服务器允许您管理 API、版本、规范、操作等。"],
    ["Connect your AI assistants to Looker business intelligence", "将您的 AI 助手连接到 Looker 商业智能，通过自然语言查询实现数据探索。"],
    ["Connect your AI assistants to the Knowledge Catalog", "将您的 AI 助手连接到 Knowledge Catalog，实现数据发现和治理。"],
    ["The MCP Toolbox for Databases is an open-source MCP server", "MCP Toolbox for Databases 是一个开源 MCP 服务器，旨在简化和保护用于与数据库交互的工具的开发。"],
    ["Interact with your Oracle Database data using natural language", "使用自然语言与您的 Oracle 数据库交互。此 MCP 服务器允许您安全地连接到您的数据库以执行 SQL 查询..."],
    ["The Dev Mode MCP Server brings Figma directly into your workflow", "Dev Mode MCP 服务器通过向从 Figma 生成代码的 AI 智能体提供重要的设计信息和上下文，将 Figma 直接带入您的工作流..."],
    ["The GitHub MCP Server is a Model Context Protocol (MCP) server", "GitHub MCP 服务器提供与 GitHub API 的无缝集成，从而实现高级自动化和..."],
    ["The Google Home Developer MCP server allows you to search", "Google Home Developer MCP 服务器允许您搜索 Google Home 文档、OpenThread 和 Matter 规范文档。"],
    ["Neon MCP Server is an open-source tool that lets you interact", "Neon MCP 服务器是一个开源工具，允许您使用自然语言与您的 Neon Postgres 数据库交互。"],
    ["The Stripe Model Context Protocol server allows you to integrate", "Stripe MCP 服务器允许您通过函数调用与 Stripe API 集成。该协议支持各种交互工具..."],
    ["Interact with Redis key-value stores", "与 Redis 键值存储交互。"],
    ["A Model Context Protocol server for interacting with MongoDB", "用于与 MongoDB Atlas 交互的模型上下文协议服务器。"],
    ["Official Notion MCP Server that allows interaction with Notion", "官方 Notion MCP 服务器，允许通过 Notion API 与 Notion 工作区、页面、数据库和评论进行交互。"],
    ["Official Linear.app MCP Server for interacting with Linear", "官方 Linear.app MCP 服务器，用于与 Linear 项目、议题和工作流进行交互。"],
    ["An MCP server implementation that integrates the Perplexity", "一个集成了 Perplexity Sonar API 的 MCP 服务器实现，以提供实时的、全网范围的研究能力。"],
    ["Official PayPal MCP Server that allows integration with PayPal", "官方 PayPal MCP 服务器，允许与 PayPal API 集成，用于支付处理、交易管理和账户操作。"],
    ["The Heroku Platform MCP Server enables seamless interaction", "Heroku Platform MCP 服务器可实现与 Heroku 平台资源的无缝交互，允许 LLM 读取、管理和操作应用程序..."],
    ["The Pinecone MCP Server enables AI tools to search Pinecone", "Pinecone MCP 服务器使 AI 工具能够搜索 Pinecone 文档、配置索引、根据索引配置生成代码..."],
    ["Connect your Supabase projects to AI assistants.", "将您的 Supabase 项目连接到 AI 助手。此 MCP 服务器允许管理表、获取配置、执行 SQL 查询、管理边缘函数等..."],
    ["The Prisma MCP Server enables AI tools to interact with Prisma", "Prisma MCP 服务器使 AI 工具能够与 Prisma 交互，从而轻松创建和管理 Postgres 数据库。"],
    ["The Locofy MCP Server", "Locofy MCP 服务器使 Locofy.ai 代码能够与您的 IDE 集成并进行扩展。"],
    ["Locofy MCP Server enables Locofy.ai code", "Locofy MCP 服务器使 Locofy.ai 代码能够与您的 IDE 集成并进行扩展。"],
    ["Airweave lets agents search any app.", "Airweave 允许智能体搜索任何应用程序。"],
    ["Atlassian MCP Server for interacting with Atlassian", "用于与 Atlassian 产品交互的 Atlassian MCP 服务器。"],
    ["Interact with your Harness account using natural language", "使用自然语言与您的 Harness 账户交互。此 MCP 服务器允许 AI 智能体检查和管理 CI/CD 流水线、执行、服务..."],
    ["SonarQube MCP Server enables AI assistants to interact", "SonarQube MCP 服务器使 AI 助手能够与 SonarQube 实例交互，进行代码质量分析、项目管理和质量门限操作。"],
    ["Perform searches on ingested data in Google-owned data stores", "在 Google 拥有的数据存储中，对已摄取的数据执行搜索。"],
    ["Interact with documents stored in a Firestore database", "使用自然语言与存储在 Firestore 数据库中的文档进行交互。"],
    ["Access resources in the Cloud Logging platform using natural", "使用自然语言访问 Cloud Logging 平台中的资源。"],
    ["Manage clusters for Managed Service for Apache Kafka", "使用自然语言管理 Apache Kafka 托管服务和 Kafka Connect 的集群。"],
    ["Access resources in the Cloud Monitoring platform using natural", "使用自然语言访问 Cloud Monitoring 平台中的资源。"],
    ["Manage Pub/Sub resources and publish messages. Create, list,", "管理 Pub/Sub 资源并发布消息。创建、列出、获取、更新和删除 Pub/Sub 主题、订阅和快照，以及发布消息..."],
    ["The Cloud Quotas MCP server allows you to view quota allocations", "Cloud Quotas MCP 服务器允许您查看配额分配、请求增加配额以及管理配额调整器配置。"],
    ["Enable Antigravity to control and inspect a live Chrome browser", "使 Antigravity 能够控制和检查实时 Chrome 浏览器，利用 Chrome DevTools 的强大功能进行可靠的自动化、深度调试..."],
    ["Netlify MCP Server enables AI assistants to interact", "Netlify MCP 服务器使 AI 助手能够与 Netlify 平台交互，以管理站点、部署、域名和其他 Web 开发工作流。"],
    ["A Model Context Protocol server that provides structured thinking", "一个模型上下文协议服务器，为 LLM 对话提供结构化思考和推理能力。"],
    ["Sonatype MCP server for interacting with our dependency management", "用于与我们的依赖项管理和安全情报平台交互的 Sonatype MCP 服务器。"],
    ["The Google Maps Platform Code Assist MCP server provides", "Google Maps Platform Code Assist MCP 服务器为您喜爱的 AI 编程助手提供最新、官方的 Google Maps Platform 文档、代码..."],
    ["This MCP server provides your LLM with docs and examples to instrument your AI apps with Arize AX", "此 MCP 服务器为您的 LLM 提供文档和示例，以便使用 Arize AX 检测您的 AI 应用。它还提供对 Arize 支持的访问。将其连接到您的 IDE..."],
    ["The Postman MCP Server connects Postman to AI tools", "Postman MCP 服务器将 Postman 连接到 AI 工具，使 AI 智能体和助手能够访问工作区、管理集合和环境..."],
    ["The Stitch MCP server enables AI assistants to interact with Stitch", "Stitch MCP 服务器使 AI 助手能够与 Stitch 交互以进行设计：从文本和图像生成 UI 设计，以及访问项目和屏幕..."],
    ["The ClickHouse MCP server enables agents to securely interact", "ClickHouse MCP 服务器使智能体能够安全地与 ClickHouse 数据库交互。它提供了一个通用接口来执行 SQL、探索数据和查看..."],
    ["Perform a range of infrastructure management tasks, including: manage virtual machine", "执行一系列基础设施管理任务，包括：管理虚拟机 (VM) 实例、管理实例组管理器和实例模板..."],
    ["Access enterprise mobility data using natural language queries", "使用关于设备队列的自然语言查询、策略合规性的自动审计以及设备集成来访问企业移动数据..."],
    ["Search your Google Cloud projects using natural language", "使用自然语言搜索您的 Google Cloud 项目。"],

    // Error and Fallback Links
    ["Kick off work on your computer and continue working", "在电脑上启动工作，并可以通过手机或其他设备继续与智能体协同工作。请在应用设置中开启“远程控制”。"],
    ["Turn on Remote Control in app settings", "请在应用设置中开启“远程控制”。"],
    ["Try Remote Control", "尝试远程控制"],
    ["Agent execution terminated due to error", "智能体执行因错误而终止。"],
    ["Confirming this undo action will make the following changes", "确认此撤销操作将做出以下更改："],
    ["Confirming this undo action will not make any code changes", "确认此撤销操作不会做出任何代码更改。"],
    ["Confirming this redo action will make the following changes", "确认此重做操作将做出以下更改："],
    ["Confirming this redo action will not make any code changes", "确认此重做操作不会做出任何代码更改。"],
    ["Undo changes up to this point", "撤销更改至此处"],
    ["Redo changes up to this point", "重做更改至此处"],
    ["Our servers are experiencing high traffic", "我们的服务器当前负载较高，请稍后重试。"],
    ["Agent terminated due to error", "智能体因错误而终止"],
    ["You can prompt the model to try again", "您可以提示模型重试，或者如果错误仍然存在，可以开启新的对话。"],
    ["for more help", " 以获取更多帮助。"],
    ["See our", "查看我们的 "]
  ];

  function translateText(text) {
    if (!text || typeof text !== 'string') return text;
    let trimmed = text.trim();
    if (!trimmed) return text;

    if (dictionary[trimmed]) {
      return text.replace(trimmed, dictionary[trimmed]);
    }
    
    // Dynamic Regex Translations
    let m;

    // v2.28 & Dynamic Notification Rules
    if (text.indexOf("Gemini 4 Argon is now available") !== -1) {
      return "Gemini 4 Argon 现已面向付费 Pro 计划订阅用户开放。";
    }
    if (text.indexOf("Choose whether to be notified when the agent needs your attention") !== -1) {
      return "选择当智能体需要您的关注或完成任务时是否接收通知。";
    }
    if (text.indexOf("Setting up WSL:") !== -1) {
      return text.replace(/Setting up WSL:\s*(.*)/g, "正在配置 WSL: $1");
    }
    if ((m = trimmed.match(/^Turn\s*(\d+)(?:\s*of\s*(\d+))?$/i))) {
      return m[2] ? text.replace(trimmed, "第 " + m[1] + " / " + m[2] + " 轮") : text.replace(trimmed, "第 " + m[1] + " 轮");
    }
    if ((m = trimmed.match(/^Jump to turn\s*(\d+)$/i))) {
      return text.replace(trimmed, "跳转至第 " + m[1] + " 轮");
    }
    if ((m = trimmed.match(/^Chapter\s*(\d+)$/i))) {
      return text.replace(trimmed, "第 " + m[1] + " 章");
    }
    if ((m = trimmed.match(/^(\d+)\s*turns?$/i))) {
      return text.replace(trimmed, m[1] + " 轮对话");
    }
    if ((m = trimmed.match(/^Page\s*(\d+)\s*of\s*(\d+)$/i))) {
      return text.replace(trimmed, "第 " + m[1] + " 页，共 " + m[2] + " 页");
    }
    if ((m = trimmed.match(/^(\d+)\s*attachments?$/i))) {
      return text.replace(trimmed, m[1] + " 个附件");
    }

    if (text.indexOf("of the customization budget is available") !== -1) {
      text = text.replace(/(\d+(?:\.\d+)?)% of the customization budget is available\.?/g, "自定义项预算可用额度为 $1%。");
      text = text.replace(/%\s*of the customization budget is available\.?/g, "% 的自定义项预算可用额度。");
      text = text.replace(/(^\s*)of the customization budget is available\.?/g, "$1的自定义项预算可用额度。");
    }
    if ((m = trimmed.match(/^Show (\d+) breakdowns?$/))) {
      return text.replace(trimmed, "显示 " + m[1] + " 项明细");
    }
    if ((m = trimmed.match(/^Explored (\d+) files? >$/))) {
      return text.replace(trimmed, "已浏览 " + m[1] + " 个文件 >");
    }
    if ((m = trimmed.match(/^Editing (.+) \+(\d+) -(\d+)$/))) {
      return text.replace(trimmed, "正在编辑 " + m[1] + " +" + m[2] + " -" + m[3]);
    }
    if ((m = trimmed.match(/^(\d+)\s+agents?\s+running$/i))) {
      return text.replace(trimmed, m[1] + " 个智能体运行中");
    }
    if (/^No\s+agents?\s+running$/i.test(trimmed)) {
      return text.replace(trimmed, "暂无运行中的智能体");
    }
    if ((m = trimmed.match(/^Start\s+Best-of-(\d+)$/i))) {
      return text.replace(trimmed, "启动 " + m[1] + " 方案优选");
    }
    if (trimmed === "Waiting for user input") {
      return text.replace(trimmed, "等待用户输入");
    }
    if ((m = trimmed.match(/^Artifacts?\s*(\d+)$/i))) {
      return text.replace(trimmed, "产物 " + m[1]);
    }
    if ((m = trimmed.match(/^No artifacts generated\.?$/i))) {
      return text.replace(trimmed, "未生成任何产物");
    }
    if (/(?:No|否)\s*(?:projects?|项目)?\s*found/i.test(text) || text.indexOf("No projects found") !== -1 || text.indexOf("No project found") !== -1) {
      return text.replace(/(?:No|否)\s*(?:projects?|项目)?\s*found\.?|No projects found\.?|No project found\.?/gi, "暂无项目");
    }
    if ((m = trimmed.match(/^(?:No|否)\s*projects?\s*found\.?$/i))) {
      return text.replace(trimmed, "暂无项目");
    }
    if ((m = trimmed.match(/^No\s+Project$/i))) {
      return text.replace(trimmed, "无项目");
    }
    if (trimmed === "Type") return text.replace(trimmed, "输入");
    if (trimmed === "and select") return text.replace(trimmed, "并选择");
    if (trimmed === "to have the agent generate a plan." || trimmed === "to have the agent generate a plan") {
      return text.replace(trimmed, "即可让智能体生成计划。");
    }
    if (trimmed === "Visit") return text.replace(trimmed, "访问");
    if (trimmed === "Legal Help") return text.replace(trimmed, "法律帮助");
    if (trimmed === "to ask for content changes for legal reasons." || trimmed === "to ask for content changes for legal reasons") {
      return text.replace(trimmed, "以出于法律原因请求更改内容。");
    }
    if ((m = trimmed.match(/^Learn more about (.+)$/))) {
      return text.replace(trimmed, "了解更多关于 " + (dictionary[m[1]] || m[1]) + " 的信息");
    }
    if ((m = trimmed.match(/^You have used some of your weekly limit, it will fully refresh in (.*)\.$/))) {
      let timeStr = m[1].replace(/days?/g, "天").replace(/hours?/g, "小时").replace(/minutes?/g, "分钟").replace(/,/g, "");
      return text.replace(trimmed, "您已使用部分每周限额，它将在 " + timeStr + " 后完全重置。");
    }
    if ((m = trimmed.match(/^You have used some of your 5-hour limit, it will fully refresh in (.*)\.$/))) {
      let timeStr = m[1].replace(/days?/g, "天").replace(/hours?/g, "小时").replace(/minutes?/g, "分钟").replace(/,/g, "");
      return text.replace(trimmed, "您已使用部分五小时限额，它将在 " + timeStr + " 后完全重置。");
    }
    if ((m = trimmed.match(/^Resets? in\s+(.+)$/i))) {
      let timeStr = m[1]
        .replace(/(\d+)\s*d(?:ays?)?/gi, "$1天 ")
        .replace(/(\d+)\s*h(?:ours?)?/gi, "$1小时 ")
        .replace(/(\d+)\s*m(?:inutes?|ins?)?/gi, "$1分钟 ")
        .replace(/(\d+)\s*s(?:econds?|ecs?)?/gi, "$1秒 ")
        .replace(/,\s*/g, " ")
        .trim();
      return text.replace(trimmed, "将在 " + timeStr + " 后重置");
    }
    if (/^Exploring\b/i.test(trimmed) || /running command/i.test(trimmed)) {
      let translatedActions = trimmed
        .replace(/Exploring file/gi, "浏览文件")
        .replace(/running command/gi, "运行命令")
        .replace(/editing file/gi, "编辑文件")
        .replace(/,\s*/g, "、");
      return text.replace(trimmed, translatedActions);
    }
    if ((m = trimmed.match(/^Files? Changed\s*(\d+)$/i))) return text.replace(trimmed, "已修改文件 " + m[1]);
    if ((m = trimmed.match(/^Uploads?\s*(\d+)$/i))) return text.replace(trimmed, "已上传文件 " + m[1]);
    if ((m = trimmed.match(/^See all\s*\((.+?)\)$/i))) return text.replace(trimmed, "查看全部 (" + m[1] + ")");
    if ((m = trimmed.match(/^Background Tasks?\s*(\d+)$/i))) return text.replace(trimmed, "后台任务 " + m[1]);
    if ((m = trimmed.match(/^Terminals?\s*(\d+)$/i))) return text.replace(trimmed, "终端 " + m[1]);
    if ((m = trimmed.match(/^No subagents?(?:\s*running)?\.?$/i))) return text.replace(trimmed, "暂无子智能体");
    if ((m = trimmed.match(/^Available AI Credits: ([\d,]+)$/))) {
      return text.replace(trimmed, "可用 AI 积分: " + m[1]);
    }
    if ((m = trimmed.match(/^Send feedback as (.+)$/))) {
      return text.replace(trimmed, "以 " + m[1] + " 的身份发送反馈");
    }
    if ((m = trimmed.match(/^(\+?\d+) more lines$/))) {
      return text.replace(trimmed, "更多 " + m[1] + " 行");
    }
    if ((m = trimmed.match(/^(\d+) files? changed$/))) {
      return text.replace(trimmed, m[1] + " 个文件已修改");
    }
    if ((m = trimmed.match(/^See (\d+) more$/i))) return text.replace(trimmed, "查看更多 " + m[1] + " 项");
    if ((m = trimmed.match(/^Last (\d+) days?$/i))) return text.replace(trimmed, "最近 " + m[1] + " 天");
    if ((m = trimmed.match(/^Last (\d+) hours?$/i))) return text.replace(trimmed, "最近 " + m[1] + " 小时");
    if ((m = trimmed.match(/^Last (\d+) months?$/i))) return text.replace(trimmed, "最近 " + m[1] + " 个月");
    if ((m = trimmed.match(/^Version ([\d\.]+(-\w+)?)$/))) {
      return text.replace(trimmed, "版本 v" + m[1]);
    }
    if ((m = trimmed.match(/^Start using (.+?), our best (.+?) model\.?$/i))) {
      return text.replace(trimmed, "开始使用 " + m[1] + "，我们最强大的 " + m[2] + " 模型。");
    }
    if (text.indexOf("is now available on paid Pro and Ultra plans") !== -1 || text.indexOf("Third-party model access will no longer be available") !== -1) {
      return "Sonnet 5.5 现已在付费的 Pro 和 Ultra 方案中提供。从 2026 年 11 月 2 日起，您当前的方案将不再支持访问第三方模型。";
    }
    if ((m = trimmed.match(/^(\d+)\s*s(?:\s*ago)?$/i))) return text.replace(trimmed, m[1] + "秒前");
    if ((m = trimmed.match(/^(\d+)\s*m(?:\s*ago)?$/i))) return text.replace(trimmed, m[1] + "分钟前");
    if ((m = trimmed.match(/^(\d+)\s*h(?:\s*ago)?$/i))) return text.replace(trimmed, m[1] + "小时前");
    if ((m = trimmed.match(/^(\d+)\s*d(?:\s*ago)?$/i))) return text.replace(trimmed, m[1] + "天前");

    // Dynamic Time Formatter
    if (text.indexOf("Worked for") !== -1) {
      return text.replace(/Worked for ([\d\.a-z ]+)/gi, function(_, timeStr) {
        let t = timeStr.replace(/ms/g, "毫秒").replace(/s/g, "秒").replace(/m/g, "分").replace(/h/g, "小时");
        return "运行耗时 " + t;
      });
    }
    if (text.indexOf("Thought for") !== -1) {
      return text.replace(/Thought for ([\d\.a-z ]+)/gi, function(_, timeStr) {
        let t = timeStr.replace(/ms/g, "毫秒").replace(/s/g, "秒").replace(/m/g, "分").replace(/h/g, "小时");
        return "思考耗时 " + t;
      });
    }
    if (text.indexOf("Working") !== -1) {
      text = text.replace(/Working(\.*)/g, "运行中$1");
    }

    // Special Multi-segment Matches
    if (text.indexOf("Google Developer Knowledge") !== -1 || text.indexOf("official developer documentation and retrieve") !== -1) {
      return "Google Developer Knowledge MCP 服务器使 AI 驱动的开发工具能够搜索 Google 的官方开发者文档并检索相关内容...";
    }
    if (text.indexOf("Ask questions. Get answers") !== -1) {
      if (text.indexOf("PostHog") !== -1) {
        return "提出问题。获取答案。该 MCP 是您的编程智能体与之对话的服务器。用英语提问，它会针对您的 PostHog 数据运行查询并返回结果。";
      }
      return "提出问题。获取答案。该 MCP 是您的 ";
    }
    if (text.indexOf("talks to. Ask a question in English") !== -1 || text.indexOf("runs the query against your") !== -1) {
      return " 与之对话的服务器。用英语提问，它会针对您的 ";
    }
    if (text.indexOf("The answer lands") !== -1 || text.indexOf("data. The answer") !== -1) {
      return " 数据运行查询并返回结果。";
    }

    if (text.indexOf("Configure the browser subagent") !== -1) {
      text = text.replace(/Configure the browser subagent\.?/g, "配置浏览器子智能体。");
    }
    if (text.indexOf("It requires") !== -1 && text.indexOf("Configure") === -1) {
      text = text.replace(/It requires\s?/g, "需要安装 ");
    }
    if (text.indexOf("to be installed.") !== -1) {
      text = text.replace(/\s?to be installed\./g, "");
    }
    if (text.indexOf("The browser subagent can be invoked by typing") !== -1) {
      text = text.replace(/The browser subagent can be invoked by typing \/browser in the conversation input box\./g, "您可以在对话输入框中输入 /browser 来调用浏览器子智能体。");
    }

    if (text.indexOf("You currently don't have any MCP Servers installed.") !== -1) {
      text = text.replace(/You currently don't have any MCP Servers installed\./g, "您目前尚未安装任何 MCP 服务器。");
    }
    if (text.indexOf("Add an MCP server above") !== -1) {
      text = text.replace(/Add an MCP server above or add a custom one via the MCP Config\./g, "请在上方添加 MCP 服务器，或通过 MCP 配置添加自定义服务器。");
    }

    // Prefix Rules Matching
    for (let i = 0; i < textPrefixRules.length; i++) {
      if (text.indexOf(textPrefixRules[i][0]) !== -1) {
        return textPrefixRules[i][1];
      }
    }

    // Short Word Exact Replacement
    let wordsCount = trimmed.split(/\s+/).length;
    if (wordsCount <= 3) {
      let lowerText = trimmed.toLowerCase();
      if (coreWords[lowerText]) {
        return text.replace(trimmed, coreWords[lowerText]);
      }
    }
    
    return text;
  }

  function checkEmptyContainer(el) {
    if (!el || el.tagName === 'BODY' || el.tagName === 'HTML') return false;
    if (el.closest && el.closest('[data-empty-handled="true"]')) return false;
    if (el.querySelector && el.querySelector('svg, button, input')) return false;
    let t = el.textContent ? el.textContent.trim() : '';
    if (!t) return false;
    let m = t.match(/^(?:No|否)\s*(.*?)\s*found\.?$/i) || t.match(/^(.*?)\s+found\.?$/i) || t === "暂无项目" || t === "暂无对话";
    if (el.__empty_handled) return false;
    if (m) {
      let target = (m[1] || '').trim().toLowerCase();
      let label = "";
      let svg = "";
      if (target === 'projects' || target === 'project' || target === '项目' || target === '' || t === '暂无项目') {
        label = "暂无项目";
        svg = '<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-1.2-1.8A2 2 0 0 0 7.55 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"></path>';
      } else if (target === 'conversations' || target === 'conversation' || target === '对话' || t === '暂无对话') {
        label = "暂无对话";
        svg = '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>';
      } else if (target === 'results' || target === 'result' || target === '结果') {
        label = "未找到结果";
        svg = '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>';
      } else if (target === 'artifacts' || target === 'artifact' || target === '产物') {
        label = "暂无产物";
        svg = '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line>';
      } else if (target === 'files' || target === 'file' || target === '文件') {
        label = "暂无文件";
        svg = '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline>';
      } else if (target === 'models' || target === 'model' || target === '模型') {
        label = "暂无模型";
        svg = '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>';
      } else if (target === 'subagents' || target === 'subagent' || target === '子智能体') {
        label = "暂无子智能体";
        svg = '<rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line>';
      }
      if (label) {
        el.setAttribute('data-empty-handled', 'true');
        el.innerHTML = '<span style="display: inline-flex; align-items: center; gap: 8px; opacity: 0.6; padding: 2px 0;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + svg + '</svg><span>' + label + '</span></span>';
        el.__empty_handled = true;
        return true;
      }
    }
    return false;
  }

  function processNode(node) {
    if (!node) return;
    if (node.nodeType === Node.TEXT_NODE) {
      // Avoid modifying code snippets, terminal streams or editor content
      if (node.parentElement && node.parentElement.closest && node.parentElement.closest('pre, code, .monaco-editor, .xterm')) {
        return;
      }
      if (node.parentElement) {
        if (checkEmptyContainer(node.parentElement) ||
            (node.parentElement.parentElement && checkEmptyContainer(node.parentElement.parentElement))) {
          return;
        }
      }
      const translated = translateText(node.textContent);
      if (translated !== node.textContent) {
        node.textContent = translated;
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE' || node.tagName === 'CODE' || node.tagName === 'PRE') return;
      if (checkEmptyContainer(node)) return;
      if (node.placeholder) {
        const translated = translateText(node.placeholder);
        if (translated !== node.placeholder) {
          node.placeholder = translated;
        }
      }
      if (node.title) {
        const translated = translateText(node.title);
        if (translated !== node.title) {
          node.title = translated;
        }
      }
      if (node.getAttribute) {
        const ariaLabel = node.getAttribute('aria-label');
        if (ariaLabel) {
          const translated = translateText(ariaLabel);
          if (translated !== ariaLabel) node.setAttribute('aria-label', translated);
        }
        const tooltip = node.getAttribute('data-tooltip') || node.getAttribute('data-title');
        if (tooltip) {
          const translated = translateText(tooltip);
          if (translated !== tooltip) {
            if (node.hasAttribute('data-tooltip')) node.setAttribute('data-tooltip', translated);
            if (node.hasAttribute('data-title')) node.setAttribute('data-title', translated);
          }
        }
      }
      if ((node.tagName === 'INPUT' || node.tagName === 'BUTTON') && typeof node.value === 'string' && node.value) {
        const translated = translateText(node.value);
        if (translated !== node.value) {
          node.value = translated;
        }
      }
      if (node.shadowRoot) {
        processNode(node.shadowRoot);
      }
      // Recursively process child nodes
      Array.from(node.childNodes).forEach(processNode);
    }
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          processNode(node);
        });
      } else if (mutation.type === 'characterData') {
        processNode(mutation.target);
      } else if (mutation.type === 'attributes') {
        processNode(mutation.target);
      }
    });
  });

  function startLocalizationEngine() {
    if (document.body) {
      processNode(document.body);
      try {
        observer.observe(document.body, {
          childList: true,
          subtree: true,
          characterData: true,
          attributes: true,
          attributeFilter: ['placeholder', 'title', 'aria-label', 'data-tooltip']
        });
      } catch (e) {}
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        if (document.body) {
          processNode(document.body);
          try {
            observer.observe(document.body, {
              childList: true,
              subtree: true,
              characterData: true,
              attributes: true,
              attributeFilter: ['placeholder', 'title', 'aria-label', 'data-tooltip']
            });
          } catch (e) {}
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startLocalizationEngine);
  } else {
    startLocalizationEngine();
  }
})();
"""

MENU_TRANSLATOR_INJECTION = r"""
// Antigravity Chinese Localization Engine - Menu
(function() {
  const menuTranslationMap = {
    'File': '文件', 'Edit': '编辑', 'View': '视图', 'Window': '窗口', 'Help': '帮助',
    'New Conversation': '新建对话', 'New Window': '新建窗口', 'Close Window': '关闭窗口',
    'Check for Updates': '检查更新', 'Checking for Updates...': '正在检查更新...',
    'Downloading Update...': '正在下载更新...', 'Restart to Update': '重启以应用更新',
    'Undo': '撤销', 'Redo': '重做', 'Cut': '剪切', 'Copy': '复制', 'Paste': '粘贴',
    'Paste and Match Style': '粘贴并匹配样式', 'Delete': '删除', 'Select All': '全选',
    'Minimize': '最小化', 'Zoom': '缩放', 'Close': '关闭', 'Quit Antigravity': '退出 Antigravity',
    'About Antigravity': '关于 Antigravity', 'Services': '服务', 'Hide Antigravity': '隐藏 Antigravity',
    'Hide Others': '隐藏其他', 'Show All': '显示全部', 'Force Reload': '强制重新加载',
    'Reload': '重新加载', 'Actual Size': '实际大小', 'Reset Zoom': '重置缩放',
    'Zoom In': '放大', 'Zoom Out': '缩小', 'Toggle Full Screen': '切换全屏',
    'Split': '分屏', 'Split Right': '向右分屏', 'Split Down': '向下分屏', 'Replace With New': '替换为新建',
    'Docs': '官方文档', 'Connect to WSL': '连接至 WSL', 'Reopen Locally': '在本地重新打开',
    'Open IDE': '打开 IDE', 'Open Antigravity': '打开 Antigravity', 'Show Antigravity': '显示 Antigravity',
    'No agents running': '暂无运行中的智能体',
    'Preferences': '偏好设置', 'Settings': '设置', 'Open Settings': '打开设置',
    'Toggle Developer Tools': '切换开发者工具', 'Developer Tools': '开发者工具',
    'Debug Console': '调试控制台', 'Bring All to Front': '前置全部窗口', 'Quit': '退出'
  };

  function translateLabelStr(lbl) {
    if (!lbl || typeof lbl !== 'string') return lbl;
    const clean = lbl.replace(/&([A-Za-z])/g, '$1');
    if (menuTranslationMap[lbl]) return menuTranslationMap[lbl];
    if (menuTranslationMap[clean]) return menuTranslationMap[clean];
    const m = clean.match(/^(\d+)\s+agents?\s+running$/i);
    if (m) return m[1] + ' 个智能体运行中';
    return lbl;
  }

  function translateMenuTree(item) {
    if (!item) return;
    if (item.label) {
      const next = translateLabelStr(item.label);
      if (next !== item.label) {
        try { item.label = next; } catch (e) {}
      }
    }
    if (item.submenu) {
      if (Array.isArray(item.submenu)) {
        item.submenu.forEach(translateMenuTree);
      } else if (Array.isArray(item.submenu.items)) {
        item.submenu.items.forEach(translateMenuTree);
      }
    }
  }

  try {
    const { Menu } = require('electron');
    if (Menu && !Menu.__isTranslated) {
      if (Menu.buildFromTemplate) {
        const origBuild = Menu.buildFromTemplate;
        Menu.buildFromTemplate = function(template) {
          if (Array.isArray(template)) {
            template.forEach(translateMenuTree);
          }
          return origBuild.call(this, template);
        };
      }
      if (Menu.setApplicationMenu) {
        const origSetAppMenu = Menu.setApplicationMenu;
        Menu.setApplicationMenu = function(menu) {
          if (menu && Array.isArray(menu.items)) {
            menu.items.forEach(translateMenuTree);
          }
          return origSetAppMenu.call(this, menu);
        };
      }
      Menu.__isTranslated = true;
    }
  } catch (e) {
    console.error("Menu hooking failed:", e);
  }
})();
"""

def extract_asar(asar_path, dest_dir):
    """Pure-Python asar archive extractor with path-traversal and bounds checks."""
    file_size = os.path.getsize(asar_path)
    if file_size < 20:
        raise ValueError("ASAR 文件过小或已损坏")
    dest_root = os.path.realpath(dest_dir)
    os.makedirs(dest_root, exist_ok=True)

    with open(asar_path, 'rb') as f:
        data = f.read(16)
        if len(data) != 16:
            raise ValueError("ASAR 文件头不完整")
        magic, size, u1, header_size = struct.unpack('<4I', data)
        if header_size <= 0 or size <= 0 or 16 + header_size > file_size:
            raise ValueError("ASAR 文件头长度非法")
        base_offset = 8 + size
        if base_offset > file_size:
            raise ValueError("ASAR 数据偏移越界")
        header_json = f.read(header_size).decode('utf-8')
        header = json.loads(header_json)
        if not isinstance(header, dict) or not isinstance(header.get('files'), dict):
            raise ValueError("ASAR 文件索引结构无效")

        def _safe_child(current_path, name):
            if not isinstance(name, str) or not name or name in ('.', '..'):
                raise ValueError(f"ASAR 非法条目名: {name!r}")
            if '/' in name or '\\' in name or '\x00' in name or os.path.isabs(name):
                raise ValueError(f"ASAR 路径穿越拦截: {name!r}")
            candidate = os.path.realpath(os.path.join(current_path, name))
            if os.path.commonpath([dest_root, candidate]) != dest_root:
                raise ValueError(f"ASAR 路径穿越拦截: {name!r}")
            return candidate

        def extract_node(node, current_path):
            os.makedirs(current_path, exist_ok=True)
            for name, info in node.items():
                if not isinstance(info, dict):
                    continue
                path = _safe_child(current_path, name)
                if 'files' in info and isinstance(info['files'], dict):
                    extract_node(info['files'], path)
                elif 'offset' in info and 'size' in info:
                    offset = int(info['offset'])
                    entry_size = int(info['size'])
                    if offset < 0 or entry_size < 0 or base_offset + offset + entry_size > file_size:
                        raise ValueError(f"ASAR 文件偏移越界: {name!r}")
                    f.seek(base_offset + offset)
                    file_data = f.read(entry_size)
                    with open(path, 'wb') as out_f:
                        out_f.write(file_data)

        extract_node(header.get('files', {}), dest_root)

def append_once(file_path, content, marker, name):
    if not os.path.exists(file_path):
        print(f"[警告] 未找到文件 {os.path.basename(file_path)}，已跳过注入 {name}。")
        return
    
    with open(file_path, "r", encoding="utf-8") as f:
        existing = f.read()
    
    if marker in existing:
        print(f"[状态] 发现已存在的 {name}，正在热更新词典...")
        idx = existing.find("// " + marker)
        if idx == -1:
            idx = existing.find(marker)
        if idx != -1:
            clean_content = existing[:idx].rstrip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_content + "\n" + content + "\n")
            print(f"[成功] 词典热更新完成：{name} ({os.path.basename(file_path)})")
        return
    
    with open(file_path, "a", encoding="utf-8") as f:
        f.write("\n" + content + "\n")
    print(f"[成功] 注入完成：{name} ({os.path.basename(file_path)})")

def remove_injected_block(file_path, marker, name):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        existing = f.read()
    if marker not in existing:
        return
    idx = existing.find("// " + marker)
    if idx == -1:
        idx = existing.find(marker)
    if idx != -1:
        clean_content = existing[:idx].rstrip() + "\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean_content)
        print(f"[恢复] 已移除旧的 {name} ({os.path.basename(file_path)})")

def replace_in_file(file_path, target, replacement):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if replacement in content:
        print(f"[跳过] 目标已替换 ({os.path.basename(file_path)})")
        return
    content = content.replace(target, replacement)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[成功] 执行目标替换 ({os.path.basename(file_path)})")

def ensure_desktop_shortcut(exe_path):
    if sys.platform != "win32" or not os.path.exists(exe_path):
        return
    desktop = get_desktop_dir()
    if not desktop or not os.path.exists(desktop):
        return
    lnk_path = os.path.join(desktop, "Antigravity.lnk")
    lnk_ps = lnk_path.replace("'", "''")
    exe_ps = exe_path.replace("'", "''")
    workdir_ps = os.path.dirname(exe_path).replace("'", "''")
    ps_cmd = (
        f"$wsh = New-Object -ComObject WScript.Shell; "
        f"$s = $wsh.CreateShortcut('{lnk_ps}'); "
        f"$existingArgs = [string]$s.Arguments; "
        f"if ($existingArgs -notmatch '(?i)--remote-debugging-port') {{ "
        f"$existingArgs = ($existingArgs + ' --remote-debugging-port=0').Trim() "
        f"}}; "
        f"$s.TargetPath = '{exe_ps}'; "
        f"$s.Arguments = $existingArgs; "
        f"$s.WorkingDirectory = '{workdir_ps}'; "
        f"$s.IconLocation = '{exe_ps},0'; "
        f"$s.Description = 'Google Antigravity'; "
        f"$s.Save()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            check=True,
            creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        print(f"[成功] 桌面快捷方式已就绪: {lnk_path}")
    except Exception as e:
        print(f"[提示] 创建桌面快捷方式跳过: {e}")


def _cleanup_temp_staging_dirs(resources_dir):
    for pattern in ("app.staging.*", "app.old.*"):
        for d in glob.glob(os.path.join(resources_dir, pattern)):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)


def _restore_update_yml(resources_dir):
    update_yml = os.path.join(resources_dir, "app-update.yml")
    disabled_yml = os.path.join(resources_dir, "app-update.yml.disabled")
    if os.path.exists(disabled_yml):
        try:
            if not os.path.exists(update_yml):
                os.rename(disabled_yml, update_yml)
                print("[恢复] 已恢复官方自动更新配置 (app-update.yml)")
            else:
                os.remove(disabled_yml)
        except Exception as e:
            print(f"[提示] 恢复更新配置出现异常: {e}")


def _inject_all_translations(target_app_dir):
    preload_path = os.path.join(target_app_dir, "dist", "preload.js")
    menu_path = os.path.join(target_app_dir, "dist", "menu.js")
    tray_path = os.path.join(target_app_dir, "dist", "tray.js")
    updater_path = os.path.join(target_app_dir, "dist", "updater.js")

    append_once(preload_path, DOM_TRANSLATOR_INJECTION, "Antigravity Chinese Localization Engine", "Web UI Injection")
    append_once(menu_path, MENU_TRANSLATOR_INJECTION, "Antigravity Chinese Localization Engine - Menu", "Menu Translator Injection")
    remove_injected_block(updater_path, "Antigravity Chinese Localization Engine - Auto Update Hook", "自动更新封锁 Hook")

    replace_in_file(tray_path, "'Show Antigravity'", "'显示 Antigravity'")
    replace_in_file(tray_path, "'Quit'", "'退出'")
    replace_in_file(
        tray_path,
        "(count > 0 ? `${count}` : 'No') +\n                    ' agent' +\n                    (count === 1 ? '' : 's') +\n                    ' running'",
        "(count > 0 ? `${count} 个智能体运行中` : '暂无运行中的智能体')"
    )

    main_js_path = os.path.join(target_app_dir, "dist", "main.js")
    replace_in_file(main_js_path, "label: 'No agents running'", "label: '暂无运行中的智能体'")
    replace_in_file(main_js_path, "label: `Open ${electron_1.app.getName()}`", "label: `打开 ${electron_1.app.getName()}`")
    replace_in_file(main_js_path, "label: 'Quit'", "label: '退出'")
    replace_in_file(main_js_path, "buttons: ['Cancel', 'Quit']", "buttons: ['取消', '退出']")
    replace_in_file(main_js_path, "title: 'Confirm Quit'", "title: '确认退出'")
    replace_in_file(main_js_path, "message: 'Are you sure you want to quit?'", "message: '确定要退出 Antigravity 吗？'")
    replace_in_file(main_js_path, "detail: 'There may be agents or background tasks running.'", "detail: '当前可能仍有智能体或后台任务正在运行。'")

    splash_path = os.path.join(target_app_dir, "dist", "provisionSplash.js")
    if os.path.exists(splash_path):
        with open(splash_path, "r", encoding="utf-8") as f:
            splash_content = f.read()
        patched_splash = splash_content.replace("Setting up WSL: ", "正在配置 WSL: ")
        if patched_splash != splash_content:
            with open(splash_path, "w", encoding="utf-8") as f:
                f.write(patched_splash)
            print(f"[成功] 已成功汉化 WSL 启动界面 ({os.path.basename(splash_path)})")

    loading_path = os.path.join(target_app_dir, "dist", "loadingOverlay.js")
    if os.path.exists(loading_path):
        with open(loading_path, "r", encoding="utf-8") as f:
            loading_content = f.read()
        patched_loading = loading_content.replace(">Loading Antigravity<", ">正在加载 Antigravity<")
        if patched_loading != loading_content:
            with open(loading_path, "w", encoding="utf-8") as f:
                f.write(patched_loading)
            print(f"[成功] 已成功汉化启动加载界面 ({os.path.basename(loading_path)})")


def apply_patch(relaunch=True):
    print("==================================================================")
    print("                                                                ")
    print("          Antigravity 桌面端 一键全量汉化与自动维护补丁           ")
    print("                                                                ")
    print("==================================================================")
    print("                                                                ")

    global APP_DIR, RESOURCES_DIR, ASAR_PATH, UNPACKED_APP_DIR
    APP_DIR = find_app_dir()
    if not APP_DIR:
        print("[错误] 未检测到 Antigravity 桌面端安装目录。")
        return False
    RESOURCES_DIR = _resolve_resources_dir(APP_DIR)
    if not RESOURCES_DIR or not os.path.isdir(RESOURCES_DIR):
        print(f"[错误] 未找到 Antigravity 资源目录: {RESOURCES_DIR}")
        return False
    ASAR_PATH = os.path.join(RESOURCES_DIR, "app.asar")
    UNPACKED_APP_DIR = os.path.join(RESOURCES_DIR, "app")
    print(f"[目录] Antigravity 路径: {APP_DIR}")

    print("[执行] 正在为您关闭 Antigravity 及语言服务进程...")
    stop_antigravity_desktop_processes(APP_DIR, wait_timeout=8.0)

    _cleanup_temp_staging_dirs(RESOURCES_DIR)

    # 1. 确保 unpacked app 文件夹就绪：新版安装时在暂存目录解包并注入后再原子替换，失败可完整回滚
    is_fresh_install = os.path.exists(ASAR_PATH)
    if is_fresh_install or not os.path.exists(UNPACKED_APP_DIR):
        source_asar = ASAR_PATH if os.path.exists(ASAR_PATH) else (ASAR_PATH + ".disabled")
        if not os.path.exists(source_asar):
            print(f"[错误] 未找到 app.asar: {ASAR_PATH}")
            return False

        if is_fresh_install and os.path.exists(UNPACKED_APP_DIR):
            print("[状态] 检测到官方新版核心包，将在临时目录重新解包并热替换...")

        staging_dir = os.path.join(RESOURCES_DIR, f"app.staging.{os.getpid()}")
        old_dir = os.path.join(RESOURCES_DIR, f"app.old.{os.getpid()}")
        try:
            print("[执行] 正在提取 app.asar 核心文件到暂存目录...")
            extract_asar(source_asar, staging_dir)
            print("[完成] 文件提取完毕.")
            _inject_all_translations(staging_dir)
        except Exception as e:
            shutil.rmtree(staging_dir, ignore_errors=True)
            print(f"[错误] 提取或注入 app.asar 失败，已保留原状态: {e}")
            return False

        moved_old = False
        try:
            if os.path.exists(UNPACKED_APP_DIR):
                os.rename(UNPACKED_APP_DIR, old_dir)
                moved_old = True
            os.rename(staging_dir, UNPACKED_APP_DIR)
        except Exception as e:
            if moved_old and not os.path.exists(UNPACKED_APP_DIR) and os.path.exists(old_dir):
                try:
                    os.rename(old_dir, UNPACKED_APP_DIR)
                except Exception:
                    pass
            shutil.rmtree(staging_dir, ignore_errors=True)
            print(f"[错误] 原子切换解包目录失败，已回滚原目录: {e}")
            return False

        if moved_old and os.path.exists(old_dir):
            shutil.rmtree(old_dir, ignore_errors=True)
    else:
        print(f"[状态] 发现已解包的工作目录: {UNPACKED_APP_DIR}")
        _inject_all_translations(UNPACKED_APP_DIR)

    # 2. 恢复官方自动更新配置（如曾被旧版补丁重命名为 .disabled，放回 app-update.yml）
    _restore_update_yml(RESOURCES_DIR)

    # 3. 禁用原生 app.asar
    if os.path.exists(ASAR_PATH):
        print("[执行] 正在禁用官方 app.asar，以强制读取汉化代码...")
        if os.path.exists(ASAR_PATH + ".disabled"):
            os.remove(ASAR_PATH + ".disabled")
        os.rename(ASAR_PATH, ASAR_PATH + ".disabled")
        print("[成功] app.asar -> app.asar.disabled")

    try:
        removed_cache = cleanup_stale_updater_cache(APP_DIR)
        if removed_cache:
            print(f"[清理] 已自动清理 {len(removed_cache)} 个已安装的旧版更新缓存文件")
    except Exception as e:
        print(f"[提示] 清理更新缓存跳过: {e}")

    print("                                                                ")
    print("==================================================================")
    print("                                                                ")
    print("       汉化补丁注入成功！                                        ")
    print("                                                                ")
    print("==================================================================")

    ensure_desktop_shortcut(os.path.join(APP_DIR, 'Antigravity.exe'))

    if relaunch:
        relaunch_antigravity(APP_DIR)
    return True

def wait_and_auto_patch_after_update():
    import time
    # 等待安装程序写入新的 app.asar (最多等待 120 秒)
    for _ in range(60):
        time.sleep(2)
        target_dir = find_app_dir()
        target_asar = os.path.join(_resolve_resources_dir(target_dir), "app.asar") if target_dir else ""
        if target_asar and os.path.exists(target_asar):
            # 再等 4 秒确保 NSIS 安装包释放完所有文件句柄
            time.sleep(4)
            was_running = is_antigravity_running()
            apply_patch(relaunch=was_running)
            return

if __name__ == "__main__":
    import time
    if "--auto-post-update" in sys.argv:
        wait_and_auto_patch_after_update()
        sys.exit(0)
    if "--delay" in sys.argv:
        idx = sys.argv.index("--delay")
        delay_sec = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 5
        time.sleep(delay_sec)
        ok = apply_patch(relaunch=True)
        sys.exit(0 if ok else 1)
    exit_code = 0
    try:
        relaunch = "--no-relaunch" not in sys.argv
        ok = apply_patch(relaunch=relaunch)
        if not ok:
            exit_code = 1
        if "--no-pause" not in sys.argv:
            input("\n执行完毕，按 Enter 键退出...")
    except KeyboardInterrupt:
        print("\n\n[提示] 用户取消操作。")
    except Exception as e:
        print(f"\n[错误] 执行过程中出现异常: {e}")
        if "--no-pause" not in sys.argv:
            input("\n按 Enter 键退出...")
        raise
    sys.exit(exit_code)
