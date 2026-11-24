"use strict";

const assert = require("assert");
const Module = require("module");
const path = require("path");

const rendererDir = process.argv[2];
if (!rendererDir) {
  throw new Error("Usage: node native_menu.cjs <rendererDir>");
}

// Faithful simulation of Electron 44.9.1 Menu / MenuItem / Tray semantics:
// - `new MenuItem(options)` internally wraps `options.click` so Electron invokes
//   `item.click(event, focusedWindow, focusedWebContents)` and the constructor
//   forwards `(item, focusedWindow, event)` to the user callback.
// - `new MenuItem({ submenu: [...] })` recursively invokes `Menu.buildFromTemplate`.
// - Native IPC `popup()` context menus may be constructed via `buildFromTemplate`.
class MockMenuItem {
  constructor(options = {}) {
    this.id = options.id || "";
    this.label = options.label || "";
    this.role = options.role || "";
    this.type = options.type || "normal";
    this.enabled = options.enabled !== undefined ? options.enabled : true;
    this.visible = options.visible !== undefined ? options.visible : true;
    this.checked = Boolean(options.checked);
    this.accelerator = options.accelerator;
    if (Array.isArray(options.submenu)) {
      this.submenu = MockMenu.buildFromTemplate(options.submenu);
    } else if (options.submenu) {
      this.submenu = options.submenu;
    }
    const userClick = typeof options.click === "function" ? options.click : null;
    this.click = (event, focusedWindow, _focusedWebContents) => {
      if (userClick) {
        return userClick(this, focusedWindow, event);
      }
    };
  }
}

class MockMenu {
  constructor(items = []) {
    this.items = items;
    this._popupCount = 0;
  }
  insert(pos, item) {
    if (!(item instanceof MockMenuItem)) {
      throw new TypeError("Invalid item");
    }
    this.items.splice(pos, 0, item);
  }
  getMenuItemById(id) {
    for (const item of this.items) {
      if (item.id === id) return item;
      const found = item.submenu?.getMenuItemById?.(id);
      if (found) return found;
    }
    return null;
  }
  popup() {
    this._popupCount++;
  }
}

let currentAppMenu = null;
let lastTrayMenu = null;

MockMenu.buildFromTemplate = function (template) {
  const menu = new MockMenu([]);
  for (const tpl of template) {
    const item = tpl instanceof MockMenuItem ? tpl : new MockMenuItem(tpl);
    menu.items.push(item);
  }
  return menu;
};

MockMenu.getApplicationMenu = function () {
  return currentAppMenu;
};

MockMenu.setApplicationMenu = function (menu) {
  currentAppMenu = menu;
};

class MockTray {
  setContextMenu(menu) {
    lastTrayMenu = menu;
  }
}

// Emulates Electron Menu._executeCommand(event, id)
function executeMenuCommand(item, event = { ctrlKey: false }) {
  return item.click(event, null, null);
}

let checkCalls = 0;
let restartCalls = 0;
const updaterMock = {
  MenuUpdateStep: {
    CheckForUpdates: "Check for Updates",
    CheckingForUpdates: "Checking for Updates...",
    DownloadingUpdate: "Downloading Update...",
    RestartToUpdate: "Restart to Update",
  },
  updateActions: {
    "Check for Updates": () => { checkCalls++; },
    "Checking for Updates...": undefined,
    "Downloading Update...": undefined,
    "Restart to Update": () => { restartCalls++; },
  },
  updateMenuState(step) {
    const menu = MockMenu.getApplicationMenu();
    const item = menu?.getMenuItemById("check-for-updates");
    if (item) {
      item.label = step;
      item.enabled = updaterMock.updateActions[step] !== undefined;
    }
  },
};

const patchedUpdaterMock = {
  updateActions: updaterMock.updateActions,
  updateMenuState(step) {
    const menu = MockMenu.getApplicationMenu();
    const item = menu?.getMenuItemById("check-for-updates");
    if (item) {
      const _agUpdateLabels = {
        "Check for Updates": "检查更新",
        "Check for Updates...": "检查更新...",
        "Checking for Updates...": "正在检查更新...",
        "Downloading Update...": "正在下载更新...",
        "Restart to Update": "重启以应用更新",
      };
      item.__agUpdateStep = step;
      item.label =
        (typeof updaterMock._agTranslateUpdateStep === "function"
          ? updaterMock._agTranslateUpdateStep(step)
          : "") ||
        _agUpdateLabels[step] ||
        step;
      item.enabled = updaterMock.updateActions[step] !== undefined;
    }
  },
};

function patchedConfigureViewZoomMenu(appMenu) {
  const viewMenuItem = appMenu.items?.find(
    (item) =>
      item.role?.toLowerCase() === "viewmenu" ||
      item.label === "View" ||
      item.__agOrigLabel === "View"
  );
  const viewSubmenu = viewMenuItem?.submenu;
  if (!viewSubmenu || !Array.isArray(viewSubmenu.items)) {
    return false;
  }
  const hasBuiltInZoomRole = viewSubmenu.items.some((item) => {
    const role = item.role?.toLowerCase();
    return role === "resetzoom" || role === "zoomin" || role === "zoomout";
  });
  if (!hasBuiltInZoomRole) return false;
  const nextItems = [];
  for (const item of viewSubmenu.items) {
    const role = item.role?.toLowerCase();
    if (role === "resetzoom") {
      nextItems.push(
        new MockMenuItem({
          id: "hub-reset-zoom",
          label: item.label || "Actual Size",
          accelerator: item.accelerator || "CmdOrCtrl+0",
        })
      );
    } else if (role === "zoomin") {
      nextItems.push(
        new MockMenuItem({
          id: "hub-zoom-in",
          label: item.label || "Zoom In",
          accelerator: item.accelerator || "CmdOrCtrl+Plus",
        }),
        new MockMenuItem({
          id: "hub-zoom-in-equal",
          label: "Zoom In",
          accelerator: "CmdOrCtrl+=",
          visible: false,
        })
      );
    } else if (role === "zoomout") {
      nextItems.push(
        new MockMenuItem({
          id: "hub-zoom-out",
          label: item.label || "Zoom Out",
          accelerator: item.accelerator || "CmdOrCtrl+-",
        })
      );
    } else {
      nextItems.push(item);
    }
  }
  viewSubmenu.items.splice(0, viewSubmenu.items.length, ...nextItems);
  return true;
}

function patchedAddItemToSubmenu(appMenu, submenuLabel, position, item) {
  const submenuItem = appMenu.items.find(
    (entry) => entry.label === submenuLabel || entry.__agOrigLabel === submenuLabel
  );
  if (!submenuItem?.submenu) {
    return false;
  }
  submenuItem.submenu.insert(position, item);
  return true;
}

const origLoad = Module._load;
Module._load = function (request) {
  if (request === "electron") {
    return {
      Menu: MockMenu,
      MenuItem: MockMenuItem,
      Tray: MockTray,
    };
  }
  if (request === "./updater") {
    return updaterMock;
  }
  return origLoad.apply(this, arguments);
};

try {
  require(path.join(rendererDir, "menu.js"));

  // 1. Electron 44.9.1 _executeCommand passes (event, window, webContents),
  // constructor passes real `this` MenuItem to user callback.
  const identityMap = new WeakMap();
  let seenMenuItem = null;
  let seenEvent = null;
  const checkItem = new MockMenuItem({
    id: "check-for-updates",
    label: updaterMock.MenuUpdateStep.CheckForUpdates,
    click: (menuItem, _win, ev) => {
      seenMenuItem = menuItem;
      seenEvent = ev;
      const action = updaterMock.updateActions[menuItem.label];
      if (action) action();
    },
  });
  identityMap.set(checkItem, "real-item");

  const appMenu = MockMenu.buildFromTemplate([
    { label: "Antigravity", submenu: [checkItem] },
    { label: "File", submenu: [{ label: "New Window" }] },
    { label: "View", submenu: [{ role: "resetzoom", label: "Actual Size" }] },
    { label: "Help", submenu: [{ label: "Docs" }] },
  ]);
  MockMenu.setApplicationMenu(appMenu);

  assert.strictEqual(checkItem.label, "检查更新");
  const syntheticEvent = { ctrlKey: true, source: "menu" };
  executeMenuCommand(checkItem, syntheticEvent);
  assert.strictEqual(checkCalls, 1);
  assert.strictEqual(seenMenuItem, checkItem);
  assert.strictEqual(identityMap.get(seenMenuItem), "real-item");
  assert.strictEqual(seenEvent, syntheticEvent);

  // Dynamic transition via updater.updateMenuState -> before & after setApplicationMenu
  updaterMock.updateMenuState(updaterMock.MenuUpdateStep.RestartToUpdate);
  executeMenuCommand(checkItem, syntheticEvent);
  assert.strictEqual(restartCalls, 1);

  MockMenu.setApplicationMenu(appMenu);
  assert.strictEqual(checkItem.label, "重启以应用更新");
  executeMenuCommand(checkItem, syntheticEvent);
  assert.strictEqual(restartCalls, 2);

  // 1b. Patched updater.updateMenuState + patched menu.js click action lookup across all 4 steps
  const liveCheckItem = new MockMenuItem({
    id: "check-for-updates",
    label: updaterMock.MenuUpdateStep.CheckForUpdates,
    click: (menuItem) => {
      const action =
        patchedUpdaterMock.updateActions[
          menuItem.__agUpdateStep ?? menuItem.__agOrigLabel ?? menuItem.label
        ];
      if (action) action();
    },
  });
  const liveMenu = MockMenu.buildFromTemplate([
    { label: "&Antigravity", submenu: [liveCheckItem] },
    { label: "&File", submenu: [{ label: "New Window" }] },
    {
      role: "viewmenu",
      label: "&View",
      submenu: [
        { role: "resetzoom", label: "Actual Size" },
        { role: "zoomin", label: "Zoom In" },
        { role: "zoomout", label: "Zoom Out" },
      ],
    },
  ]);
  // Simulate startup BEFORE configureViewZoomMenu runs (menu already translated!)
  MockMenu.setApplicationMenu(liveMenu);
  assert.strictEqual(liveMenu.items[1].label, "文件");
  assert.strictEqual(liveMenu.items[1].__agOrigLabel, "File");
  assert.strictEqual(liveMenu.items[2].label, "视图");
  assert.strictEqual(liveMenu.items[2].__agOrigLabel, "View");

  assert.strictEqual(patchedConfigureViewZoomMenu(MockMenu.getApplicationMenu()), true);
  MockMenu.setApplicationMenu(liveMenu);
  const resetZoom = liveMenu.getMenuItemById("hub-reset-zoom");
  const zoomIn = liveMenu.getMenuItemById("hub-zoom-in");
  const zoomInEqual = liveMenu.getMenuItemById("hub-zoom-in-equal");
  const zoomOut = liveMenu.getMenuItemById("hub-zoom-out");
  assert.ok(resetZoom && zoomIn && zoomInEqual && zoomOut);
  assert.strictEqual(resetZoom.label, "实际大小");
  assert.strictEqual(zoomIn.label, "放大");
  assert.strictEqual(zoomInEqual.visible, false);
  assert.strictEqual(zoomOut.label, "缩小");

  // Also test View menu matched by __agOrigLabel without role
  const noRoleMenu = MockMenu.buildFromTemplate([
    {
      label: "View",
      submenu: [{ role: "resetzoom", label: "Actual Size" }],
    },
  ]);
  MockMenu.setApplicationMenu(noRoleMenu);
  assert.strictEqual(noRoleMenu.items[0].label, "视图");
  assert.strictEqual(patchedConfigureViewZoomMenu(noRoleMenu), true);
  assert.ok(noRoleMenu.getMenuItemById("hub-reset-zoom"));

  // Restore MockMenu.getApplicationMenu() back to liveMenu for updater transitions
  MockMenu.setApplicationMenu(liveMenu);
  patchedUpdaterMock.updateMenuState(updaterMock.MenuUpdateStep.CheckingForUpdates);
  assert.strictEqual(liveCheckItem.label, "正在检查更新...");
  assert.strictEqual(liveCheckItem.enabled, false);
  assert.strictEqual(liveCheckItem.__agUpdateStep, updaterMock.MenuUpdateStep.CheckingForUpdates);

  patchedUpdaterMock.updateMenuState(updaterMock.MenuUpdateStep.DownloadingUpdate);
  assert.strictEqual(liveCheckItem.label, "正在下载更新...");
  assert.strictEqual(liveCheckItem.enabled, false);

  patchedUpdaterMock.updateMenuState(updaterMock.MenuUpdateStep.RestartToUpdate);
  assert.strictEqual(liveCheckItem.label, "重启以应用更新");
  assert.strictEqual(liveCheckItem.enabled, true);
  executeMenuCommand(liveCheckItem, syntheticEvent);
  assert.strictEqual(restartCalls, 3);

  MockMenu.setApplicationMenu(liveMenu);
  assert.strictEqual(liveCheckItem.label, "重启以应用更新");
  assert.strictEqual(liveCheckItem.__agOrigLabel, updaterMock.MenuUpdateStep.RestartToUpdate);
  executeMenuCommand(liveCheckItem, syntheticEvent);
  assert.strictEqual(restartCalls, 4);

  patchedUpdaterMock.updateMenuState(updaterMock.MenuUpdateStep.CheckForUpdates);
  assert.strictEqual(liveCheckItem.label, "检查更新");
  executeMenuCommand(liveCheckItem, syntheticEvent);
  assert.strictEqual(checkCalls, 2);

  // 2. Async Windows WSL submenu: `new MenuItem({ submenu: [...] })` invokes
  // Menu.buildFromTemplate directly, so global hook must NOT translate WSL distros.
  const wslMenuItem = new MockMenuItem({
    label: "Connect to WSL",
    submenu: [
      { label: "Ubuntu" },
      { label: "Settings" },
      { label: "Default" },
    ],
  });
  assert.strictEqual(wslMenuItem.submenu.items[0].label, "Ubuntu");
  assert.strictEqual(wslMenuItem.submenu.items[1].label, "Settings");
  assert.strictEqual(wslMenuItem.submenu.items[2].label, "Default");

  assert.strictEqual(patchedAddItemToSubmenu(appMenu, "File", 1, wslMenuItem), true);
  MockMenu.setApplicationMenu(appMenu);
  assert.strictEqual(wslMenuItem.label, "连接至 WSL");
  assert.strictEqual(wslMenuItem.submenu.items[0].label, "Ubuntu");
  assert.strictEqual(wslMenuItem.submenu.items[1].label, "Settings");
  assert.strictEqual(wslMenuItem.submenu.items[2].label, "Default");

  // 3. Renderer IPC popup context menu (`Move to Group`) must preserve group names like Settings/Default
  const ctxMenu = MockMenu.buildFromTemplate([
    {
      label: "Move to Group",
      submenu: [{ label: "Settings" }, { label: "Default" }],
    },
  ]);
  ctxMenu.popup();
  assert.strictEqual(ctxMenu.items[0].submenu.items[0].label, "Settings");
  assert.strictEqual(ctxMenu.items[0].submenu.items[1].label, "Default");

  // 4. Tray context menu updates translate top-level items & protect distro names
  const tray = new MockTray();
  const trayMenu = MockMenu.buildFromTemplate([
    { label: "Open Antigravity" },
    { label: "No agents running" },
  ]);
  tray.setContextMenu(trayMenu);
  assert.strictEqual(lastTrayMenu.items[0].label, "打开 Antigravity");
  assert.strictEqual(lastTrayMenu.items[1].label, "暂无运行中的智能体");

  trayMenu.insert(
    1,
    new MockMenuItem({
      label: "Connect to WSL",
      submenu: [{ label: "Settings" }, { label: "Default" }],
    })
  );
  trayMenu.insert(2, new MockMenuItem({ label: "Reopen Locally" }));
  tray.setContextMenu(trayMenu);

  assert.strictEqual(lastTrayMenu.items[1].label, "连接至 WSL");
  assert.strictEqual(lastTrayMenu.items[1].submenu.items[0].label, "Settings");
  assert.strictEqual(lastTrayMenu.items[1].submenu.items[1].label, "Default");
  assert.strictEqual(lastTrayMenu.items[2].label, "在本地重新打开");

  console.log("native_menu.cjs: all assertions passed");
} finally {
  Module._load = origLoad;
}
