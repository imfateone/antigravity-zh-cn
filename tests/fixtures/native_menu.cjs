"use strict";

const assert = require("assert");
const fs = require("fs");
const Module = require("module");
const path = require("path");

const rendererDir = process.argv[2];
if (!rendererDir) {
  throw new Error("Usage: node native_menu.cjs <rendererDir>");
}

class MockMenuItem {
  constructor(options = {}) {
    Object.assign(this, options);
  }
}

class MockMenu {
  constructor(items = []) {
    this.items = items;
  }
  insert(pos, item) {
    this.items.splice(pos, 0, item);
  }
}

let currentAppMenu = null;
let lastTrayMenu = null;

function buildSubmenu(spec) {
  if (!Array.isArray(spec)) return spec;
  const sub = new MockMenu([]);
  for (const entry of spec) {
    const item = entry instanceof MockMenuItem ? entry : new MockMenuItem(entry);
    if (Array.isArray(item.submenu)) {
      item.submenu = buildSubmenu(item.submenu);
    }
    sub.items.push(item);
  }
  return sub;
}

MockMenu.buildFromTemplate = function (template) {
  const menu = new MockMenu([]);
  for (const tpl of template) {
    const item = tpl instanceof MockMenuItem ? tpl : new MockMenuItem(tpl);
    if (Array.isArray(item.submenu)) {
      item.submenu = buildSubmenu(item.submenu);
    }
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

const origLoad = Module._load;
Module._load = function (request) {
  if (request === "electron") {
    return {
      Menu: MockMenu,
      MenuItem: MockMenuItem,
      Tray: MockTray,
    };
  }
  return origLoad.apply(this, arguments);
};

try {
  require(path.join(rendererDir, "menu.js"));

  // 1. macOS Check for Updates / Restart to Update action lookup must still use English keys
  let checkCalls = 0;
  let restartCalls = 0;
  const updateActions = {
    "Check for Updates": () => { checkCalls++; },
    "Restart to Update": () => { restartCalls++; },
  };
  const checkItem = new MockMenuItem({
    id: "check-for-updates",
    label: "Check for Updates",
    click: (menuItem) => {
      const fn = updateActions[menuItem.label];
      if (fn) fn();
    },
  });

  const appMenu = MockMenu.buildFromTemplate([
    { label: "Antigravity", submenu: [checkItem] },
    { label: "File", submenu: [{ label: "New Window" }] },
    { label: "View", submenu: [{ role: "resetzoom", label: "Actual Size" }] },
    { label: "Help", submenu: [{ label: "Docs" }] },
  ]);
  MockMenu.setApplicationMenu(appMenu);

  assert.strictEqual(checkItem.label, "检查更新");
  checkItem.click(checkItem);
  assert.strictEqual(checkCalls, 1);

  // Even when updater mutates item.label before or after setApplicationMenu
  checkItem.label = "Restart to Update";
  checkItem.click(checkItem);
  assert.strictEqual(restartCalls, 1);

  MockMenu.setApplicationMenu(appMenu);
  assert.strictEqual(checkItem.label, "重启以应用更新");
  checkItem.click(checkItem);
  assert.strictEqual(restartCalls, 2);

  // 2. Async Windows WSL submenu lookup (`find(item => item.label === 'File')`) & distro name protection
  const fileMenuItem = appMenu.items.find((item) => item.label === "File");
  assert.ok(fileMenuItem, "File menu must still be discoverable after localization");
  assert.strictEqual(fileMenuItem.label, "文件");

  const viewMenuItem = appMenu.items.find((item) => item.label === "View");
  assert.ok(viewMenuItem, "View menu must still be discoverable after localization");
  assert.strictEqual(viewMenuItem.label, "视图");

  const wslMenuItem = new MockMenuItem({
    label: "Connect to WSL",
    submenu: buildSubmenu([
      { label: "Ubuntu" },
      { label: "Settings" },
      { label: "Default" },
    ]),
  });
  fileMenuItem.submenu.insert(1, wslMenuItem);
  MockMenu.setApplicationMenu(appMenu);

  assert.strictEqual(wslMenuItem.label, "连接至 WSL");
  assert.strictEqual(wslMenuItem.submenu.items[0].label, "Ubuntu");
  assert.strictEqual(wslMenuItem.submenu.items[1].label, "Settings");
  assert.strictEqual(wslMenuItem.submenu.items[2].label, "Default");

  // 3. Tray context menu updates translate Connect to WSL while protecting distro labels
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
      submenu: buildSubmenu([{ label: "Settings" }, { label: "Default" }]),
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
