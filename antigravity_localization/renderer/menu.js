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

  function translateLabelStr(lbl) {
    if (!lbl || typeof lbl !== 'string') return lbl;
    const clean = lbl.replace(/&([A-Za-z])/g, '$1');
    if (menuTranslationMap.has(lbl)) return menuTranslationMap.get(lbl);
    if (menuTranslationMap.has(clean)) return menuTranslationMap.get(clean);
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
