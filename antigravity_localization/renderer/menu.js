// Antigravity Chinese Localization Engine - Menu
(function() {
  const menuTranslationMap = new Map(Object.entries({
    'File': '文件', 'Edit': '编辑', 'View': '视图', 'Window': '窗口', 'Help': '帮助',
    'Workspace': '工作区', 'Create Project': '创建项目', 'Command Palette': '命令面板',
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
  }));

  const UPDATE_STEP_ALIASES = [
    ['Check for Updates', '检查更新'],
    ['Checking for Updates...', '正在检查更新...'],
    ['Downloading Update...', '正在下载更新...'],
    ['Restart to Update', '重启以应用更新'],
  ];

  // WSL distro submenus hold dynamic user/distro names (e.g. Ubuntu, Default, Settings)
  // that must never be localized when translating the parent item.
  const SKIP_SUBMENU_PARENTS = new Set(['Connect to WSL', '连接至 WSL']);

  function translateLabelStr(lbl) {
    if (!lbl || typeof lbl !== 'string') return lbl;
    const clean = lbl.replace(/&([A-Za-z])/g, '$1');
    if (menuTranslationMap.has(lbl)) return menuTranslationMap.get(lbl);
    if (menuTranslationMap.has(clean)) return menuTranslationMap.get(clean);
    const m = clean.match(/^(\d+)\s+agents?\s+running$/i);
    if (m) return m[1] + ' 个智能体运行中';
    return lbl;
  }

  function patchUpdaterActions() {
    try {
      const updater = require('./updater');
      try { if (updater && typeof updater === 'object') updater._agTranslateUpdateStep = translateLabelStr; } catch (_) {}
      const actions = updater && updater.updateActions;
      if (!actions || typeof actions !== 'object') return;
      for (const [en, zh] of UPDATE_STEP_ALIASES) {
        if (
          Object.prototype.hasOwnProperty.call(actions, en) &&
          !Object.prototype.hasOwnProperty.call(actions, zh)
        ) {
          Object.defineProperty(actions, zh, {
            configurable: true,
            enumerable: false,
            get() {
              return actions[en];
            },
          });
        }
      }
    } catch (_) {}
  }

  function translateMenuTree(item) {
    if (!item || typeof item !== 'object') return;
    const labelStr = typeof item.label === 'string' ? item.label : '';
    const hasStep = item.id === 'check-for-updates' && typeof item.__agUpdateStep === 'string' && item.__agUpdateStep;
    const translatedCurrent = labelStr ? translateLabelStr(labelStr) : labelStr;
    const origLabel = hasStep
      ? item.__agUpdateStep
      : (labelStr && translatedCurrent !== labelStr
          ? labelStr
          : (typeof item.__agOrigLabel === 'string' ? item.__agOrigLabel : labelStr));
    if (labelStr) {
      const sourceLabel = hasStep ? item.__agUpdateStep : labelStr;
      const next = translateLabelStr(sourceLabel);
      const cleanOrig = (origLabel || labelStr).replace(/&([A-Za-z])/g, '$1');
      if ((cleanOrig && item.__agOrigLabel !== cleanOrig && (next !== labelStr || hasStep)) || next !== labelStr) {
        try {
          Object.defineProperty(item, '__agOrigLabel', {
            value: cleanOrig,
            writable: true,
            configurable: true,
            enumerable: false,
          });
        } catch (_) {}
      }
      if (next !== labelStr) {
        try { item.label = next; } catch (_) {}
      }
    }

    if (SKIP_SUBMENU_PARENTS.has(origLabel) || SKIP_SUBMENU_PARENTS.has(item.label)) {
      return;
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
    patchUpdaterActions();
    const { Menu, Tray } = require('electron');
    if (Menu && !Menu.__isTranslated) {
      if (Menu.setApplicationMenu) {
        const origSetAppMenu = Menu.setApplicationMenu;
        Menu.setApplicationMenu = function(menu) {
          patchUpdaterActions();
          if (menu && Array.isArray(menu.items)) {
            menu.items.forEach(translateMenuTree);
          }
          return origSetAppMenu.call(this, menu);
        };
      }
      Menu.__isTranslated = true;
    }
    if (Tray && Tray.prototype && typeof Tray.prototype.setContextMenu === 'function' && !Tray.prototype.__agTrayTranslated) {
      const origSetContextMenu = Tray.prototype.setContextMenu;
      Tray.prototype.setContextMenu = function(menu) {
        if (menu && Array.isArray(menu.items)) {
          menu.items.forEach(translateMenuTree);
        }
        return origSetContextMenu.call(this, menu);
      };
      Tray.prototype.__agTrayTranslated = true;
    }
  } catch (e) {
    console.error("Menu hooking failed:", e);
  }
})();
