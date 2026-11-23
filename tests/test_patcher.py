# coding: utf-8
import importlib.util
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_DIR = Path(__file__).resolve().parent.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

import _ag_common
import Restore


def _load_patcher():
    spec = importlib.util.spec_from_file_location("antigravity_patcher", REPO_DIR / "Antigravity-Patcher.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


Patcher = _load_patcher()


def _build_synthetic_asar(out_path: Path, files_content: dict[str, bytes]) -> None:
    """Build a minimal valid Electron .asar archive (supports flat or 1-level relative keys)."""
    tree: dict = {}
    blobs: list[bytes] = []
    offset = 0
    for rel, content in files_content.items():
        parts = rel.split("/")
        cur = tree
        for folder in parts[:-1]:
            cur = cur.setdefault(folder, {"files": {}})["files"]
        cur[parts[-1]] = {"size": len(content), "offset": str(offset)}
        blobs.append(content)
        offset += len(content)

    header_bytes = json.dumps({"files": tree}, separators=(",", ":")).encode("utf-8")
    pad = (-len(header_bytes)) % 4
    header_padded = header_bytes + (b"\x00" * pad)
    header_section = struct.pack("<I", len(header_bytes)) + header_padded
    preamble = struct.pack("<III", 4, len(header_section) + 4, len(header_section))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(preamble + header_section + b"".join(blobs))


def _build_malicious_asar(out_path: Path, bad_name: str) -> None:
    content = b"pwned"
    header = {"files": {bad_name: {"size": len(content), "offset": "0"}}}
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    pad = (-len(header_bytes)) % 4
    header_padded = header_bytes + (b"\x00" * pad)
    header_section = struct.pack("<I", len(header_bytes)) + header_padded
    preamble = struct.pack("<III", 4, len(header_section) + 4, len(header_section))
    out_path.write_bytes(preamble + header_section + content)


class TestAntigravityZhPatcher(unittest.TestCase):
    def test_extract_asar_normal_and_blocks_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            asar_ok = root / "ok.asar"
            _build_synthetic_asar(
                asar_ok,
                {
                    "package.json": b'{"name":"antigravity","version":"2.34.0"}',
                    "dist/preload.js": b"// preload base\n",
                },
            )
            dest = root / "out"
            Patcher.extract_asar(str(asar_ok), str(dest))
            self.assertEqual(json.loads((dest / "package.json").read_text(encoding="utf-8"))["version"], "2.34.0")
            self.assertTrue((dest / "dist" / "preload.js").is_file())

            for evil_name in ("../escape.txt", r"..\escape.txt", "/abs.txt", "a/b.txt", ".."):
                evil_asar = root / "evil.asar"
                _build_malicious_asar(evil_asar, evil_name)
                with self.assertRaises(ValueError):
                    Patcher.extract_asar(str(evil_asar), str(root / "dest_evil"))
                self.assertFalse((root / "escape.txt").exists())

    def test_apply_patch_normal_and_rollback_on_failure(self):
        with tempfile.TemporaryDirectory() as td:
            app_dir = Path(td) / "Antigravity"
            res_dir = app_dir / "resources"
            res_dir.mkdir(parents=True)
            asar_path = res_dir / "app.asar"
            _build_synthetic_asar(
                asar_path,
                {
                    "package.json": b'{"name":"antigravity","version":"2.34.0"}',
                    "dist/preload.js": b"console.log('preload');\n",
                    "dist/menu.js": b"console.log('menu');\n",
                    "dist/updater.js": b"exports.init = () => {};\n",
                    "dist/tray.js": b"const a = 'Show Antigravity'; const b = 'Quit';\n",
                    "dist/main.js": b"const q = { title: 'Confirm Quit' };\n",
                },
            )
            (res_dir / "app-update.yml.disabled").write_text("provider: generic\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Patcher, "stop_antigravity_desktop_processes", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "ensure_desktop_shortcut", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "cleanup_stale_updater_cache", lambda *a, **kw: []):
                ok = Patcher.apply_patch(relaunch=False)

            self.assertTrue(ok)
            self.assertFalse(asar_path.exists())
            self.assertTrue((res_dir / "app.asar.disabled").is_file())
            self.assertTrue((res_dir / "app-update.yml").is_file())
            self.assertFalse((res_dir / "app-update.yml.disabled").exists())
            self.assertIn(
                "Antigravity Chinese Localization Engine",
                (res_dir / "app" / "dist" / "preload.js").read_text(encoding="utf-8"),
            )
            self.assertEqual(_ag_common.read_installed_ag_version(str(app_dir)), "2.34.0")

            # Simulate an official update delivering a corrupt app.asar while unpacked app exists:
            # rollback must keep existing unpacked app & new app.asar intact and leave no staging dir.
            asar_path.write_bytes(b"corrupt-new-asar-not-valid")
            marker_file = res_dir / "app" / "keep_me.txt"
            marker_file.write_text("existing-app-preserved", encoding="utf-8")

            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Patcher, "stop_antigravity_desktop_processes", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "ensure_desktop_shortcut", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "cleanup_stale_updater_cache", lambda *a, **kw: []):
                ok_fail = Patcher.apply_patch(relaunch=False)

            self.assertFalse(ok_fail)
            self.assertEqual(marker_file.read_text(encoding="utf-8"), "existing-app-preserved")
            self.assertTrue(asar_path.exists())
            self.assertEqual(list(res_dir.glob("app.staging.*")), [])

    def test_restore_preserves_newer_official_asar_and_handles_missing(self):
        with tempfile.TemporaryDirectory() as td:
            app_dir = Path(td) / "Antigravity"
            res_dir = app_dir / "resources"
            res_dir.mkdir(parents=True)

            # Case A: Both valid official app.asar (2.34.0) and stale app.asar.disabled (2.33.0) exist
            asar_path = res_dir / "app.asar"
            disabled_path = res_dir / "app.asar.disabled"
            unpacked_dir = res_dir / "app"
            _build_synthetic_asar(asar_path, {"package.json": b'{"version":"2.34.0"}'})
            _build_synthetic_asar(disabled_path, {"package.json": b'{"version":"2.33.0"}'})
            unpacked_dir.mkdir()
            (unpacked_dir / "old.txt").write_text("old", encoding="utf-8")

            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Restore, "stop_antigravity_desktop_processes", lambda *a, **kw: None):
                self.assertTrue(Restore.restore(relaunch=False))

            self.assertTrue(asar_path.is_file())
            self.assertEqual(_ag_common.read_installed_ag_version(str(app_dir)), "2.34.0")
            self.assertFalse(disabled_path.exists())
            self.assertFalse(unpacked_dir.exists())

            # Case B: Normal patched state (only app.asar.disabled + unpacked app)
            asar_path.rename(disabled_path)
            unpacked_dir.mkdir()
            (unpacked_dir / "patched.txt").write_text("zh", encoding="utf-8")
            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Restore, "stop_antigravity_desktop_processes", lambda *a, **kw: None):
                self.assertTrue(Restore.restore(relaunch=False))
            self.assertTrue(asar_path.is_file())
            self.assertFalse(disabled_path.exists())
            self.assertFalse(unpacked_dir.exists())

            # Case C: Neither app.asar nor app.asar.disabled exists -> refuse to delete unpacked app
            asar_path.unlink()
            unpacked_dir.mkdir()
            (unpacked_dir / "only_copy.txt").write_text("keep", encoding="utf-8")
            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Restore, "stop_antigravity_desktop_processes", lambda *a, **kw: None):
                self.assertFalse(Restore.restore(relaunch=False))
            self.assertTrue((unpacked_dir / "only_copy.txt").is_file())

    def test_cleanup_stale_updater_cache_version_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            app_dir = root / "Antigravity"
            pkg_dir = app_dir / "resources" / "app"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "package.json").write_text('{"version":"2.34.0"}', encoding="utf-8")

            updater_dir = root / "updater"
            pending_dir = updater_dir / "pending"
            pending_dir.mkdir(parents=True)

            inst = updater_dir / "installer.exe"
            pend_old = pending_dir / "Antigravity-2.34.0.exe"
            pend_new = pending_dir / "Antigravity-2.35.0.exe"
            info_json = pending_dir / "update-info.json"

            inst.write_bytes(b"exe")
            pend_old.write_bytes(b"exe")
            pend_new.write_bytes(b"exe")
            info_json.write_text('{"fileName":"Antigravity-2.35.0.exe"}', encoding="utf-8")

            versions = {
                str(inst): "2.34.0",
                str(pend_old): "2.34.0",
                str(pend_new): "2.35.0",
            }
            removed = _ag_common.cleanup_stale_updater_cache(
                str(app_dir),
                updater_dir=str(updater_dir),
                version_reader=lambda p: versions.get(p, ""),
            )
            self.assertIn(str(inst), removed)
            self.assertIn(str(pend_old), removed)
            self.assertFalse(inst.exists())
            self.assertFalse(pend_old.exists())
            # Newer pending installer (2.35.0 > 2.34.0) and its update-info.json must be preserved!
            self.assertTrue(pend_new.exists())
            self.assertTrue(info_json.exists())

            # Once installed becomes 2.35.0, the 2.35.0 installer & update-info.json are cleaned too
            (pkg_dir / "package.json").write_text('{"version":"2.35.0"}', encoding="utf-8")
            removed2 = _ag_common.cleanup_stale_updater_cache(
                str(app_dir),
                updater_dir=str(updater_dir),
                version_reader=lambda p: versions.get(p, ""),
            )
            self.assertIn(str(pend_new), removed2)
            self.assertIn(str(info_json), removed2)
            self.assertFalse(pend_new.exists())
            self.assertFalse(info_json.exists())

    def test_cross_process_lock_blocks_concurrent_patch_and_recovers_stale_lock(self):
        with tempfile.TemporaryDirectory() as td:
            app_dir = Path(td) / "Antigravity"
            res_dir = app_dir / "resources"
            res_dir.mkdir(parents=True)
            asar_path = res_dir / "app.asar"
            _build_synthetic_asar(
                asar_path,
                {
                    "package.json": b'{"version":"2.34.0"}',
                    "dist/preload.js": b"// preload\n",
                    "dist/menu.js": b"// menu\n",
                },
            )

            # While lock is held, both apply_patch & restore return False without modifying files
            with _ag_common.acquire_app_lock(str(res_dir)):
                with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}):
                    self.assertFalse(Patcher.apply_patch(relaunch=False))
                    self.assertFalse(Restore.restore(relaunch=False))
                self.assertTrue(asar_path.is_file())
                self.assertFalse((res_dir / "app.asar.disabled").exists())

            # Dead-PID stale lock is automatically cleaned and lock acquisition succeeds
            lock_path = res_dir / ".ag-zh-patch.lock"
            lock_path.write_text('{"pid": 99999999, "ts": 1}', encoding="utf-8")
            with _ag_common.acquire_app_lock(str(res_dir)):
                self.assertTrue(lock_path.is_file())
            self.assertFalse(lock_path.exists())

    def test_localization_skips_chat_content_and_preserves_2d_3d_tokens(self):
        """运行真实 DOM_TRANSLATOR_INJECTION JS，验证不篡改对话正文与 2D/3D/1M/2H，同时正常汉化 UI 壳子。"""
        import shutil
        import subprocess

        node_exe = shutil.which("node")
        if not node_exe:
            self.skipTest("node not installed")

        harness = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const scriptSrc = fs.readFileSync(process.argv[2], 'utf8');

function matchSingle(el, sel) {
  sel = sel.trim();
  if (!sel || !el || el.nodeType !== 1) return false;
  if (sel.startsWith('#')) return el.id === sel.slice(1);
  if (sel.startsWith('.')) {
    const cls = sel.slice(1).replace(/\\/g, '');
    return String(el.className || '').split(/\s+/).includes(cls);
  }
  const attrEq = sel.match(/^\[([^=\]]+)="([^"]*)"\]$/);
  if (attrEq) return el.getAttribute(attrEq[1]) === attrEq[2];
  const attrContains = sel.match(/^\[([^=\]]+)\*="([^"]*)"\]$/);
  if (attrContains) {
    const v = attrContains[1] === 'class' ? String(el.className || '') : String(el.getAttribute(attrContains[1]) || '');
    return v.includes(attrContains[2]);
  }
  const attrHas = sel.match(/^\[([^\]]+)\]$/);
  if (attrHas) return el.hasAttribute(attrHas[1]);
  return el.tagName === sel.toUpperCase();
}

function makeEl(tag, opts = {}) {
  const attrs = Object.assign({}, opts.attrs || {});
  const el = {
    nodeType: 1,
    tagName: tag.toUpperCase(),
    id: opts.id || '',
    className: opts.className || '',
    type: opts.type || '',
    placeholder: opts.placeholder || '',
    title: opts.title || '',
    value: opts.value || '',
    parentElement: null,
    childNodes: [],
    appendChild(child) {
      child.parentElement = el;
      el.childNodes.push(child);
      return child;
    },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    setAttribute(k, v) { attrs[k] = String(v); },
    hasAttribute(k) { return Object.prototype.hasOwnProperty.call(attrs, k); },
    matches(selector) {
      return selector.split(',').some(part => matchSingle(el, part));
    },
    closest(selector) {
      let cur = el;
      while (cur) {
        if (cur.matches(selector)) return cur;
        cur = cur.parentElement;
      }
      return null;
    },
    querySelector() { return null; },
    get textContent() {
      return el.childNodes.map(c => c.textContent).join('');
    },
  };
  return el;
}

function makeText(s) {
  return { nodeType: 3, textContent: s, parentElement: null };
}

const body = makeEl('body');

// 1. UI chrome (MUST translate)
const sidebarSpan2d = makeEl('span'); sidebarSpan2d.appendChild(makeText('2d'));
const sidebarSpan5h = makeEl('span'); sidebarSpan5h.appendChild(makeText('5h'));
const sidebarSpanAgo = makeEl('span'); sidebarSpanAgo.appendChild(makeText('3d ago'));
const uiSpan2D = makeEl('span'); uiSpan2D.appendChild(makeText('2D'));
const uiSpan3D = makeEl('span'); uiSpan3D.appendChild(makeText('3D'));
const uiSpan1M = makeEl('span'); uiSpan1M.appendChild(makeText('1M'));
const uiSpan2H = makeEl('span'); uiSpan2H.appendChild(makeText('2H'));
const uiSpan5S = makeEl('span'); uiSpan5S.appendChild(makeText('5S'));
const uiSpanWorking = makeEl('span'); uiSpanWorking.appendChild(makeText('Working...'));
const uiSpanWorkDir = makeEl('span'); uiSpanWorkDir.appendChild(makeText('Working directory'));
const uiSpanThought = makeEl('span'); uiSpanThought.appendChild(makeText('Thought for 5s'));
const uiBtnSave = makeEl('button'); uiBtnSave.appendChild(makeText('Save'));
const uiTextInput = makeEl('input', { type: 'text', value: 'error', placeholder: 'Search' });
const uiTextarea = makeEl('textarea', { placeholder: 'Search' });
uiTextarea.appendChild(makeText('2d'));

// 2. Chat markdown & user bubble & AGY monitor (MUST NOT translate content)
const prose = makeEl('div', { className: 'prose prose-sm' });
const proseP = makeEl('p'); proseP.appendChild(makeText('2D'));
const proseTd = makeEl('td'); proseTd.appendChild(makeText('true'));
const proseStrong = makeEl('strong'); proseStrong.appendChild(makeText('2d'));
const proseWorking = makeEl('span'); proseWorking.appendChild(makeText('Working...'));
prose.appendChild(proseP); prose.appendChild(proseTd); prose.appendChild(proseStrong); prose.appendChild(proseWorking);

const userBubble = makeEl('div', { className: 'group/user-input-step' });
const userText = makeEl('div'); userText.appendChild(makeText('3D'));
const userErr = makeEl('span'); userErr.appendChild(makeText('error'));
userBubble.appendChild(userText); userBubble.appendChild(userErr);

const plainTable = makeEl('table');
const plainTd5h = makeEl('td'); plainTd5h.appendChild(makeText('5h'));
const plainTdBool = makeEl('td'); plainTdBool.appendChild(makeText('false'));
plainTable.appendChild(plainTd5h); plainTable.appendChild(plainTdBool);

const agyHost = makeEl('div', { id: 'agy-monitor-footer-host' });
const agy5h = makeEl('span'); agy5h.appendChild(makeText('5h'));
agyHost.appendChild(agy5h);

for (const n of [
  sidebarSpan2d, sidebarSpan5h, sidebarSpanAgo,
  uiSpan2D, uiSpan3D, uiSpan1M, uiSpan2H, uiSpan5S,
  uiSpanWorking, uiSpanWorkDir, uiSpanThought, uiBtnSave,
  uiTextInput, uiTextarea,
  prose, userBubble, plainTable, agyHost,
]) body.appendChild(n);

const ctx = {
  window: {},
  document: { body, readyState: 'complete', addEventListener() {} },
  Node: { ELEMENT_NODE: 1, TEXT_NODE: 3 },
  MutationObserver: class { observe() {} },
  console,
  Set,
};
ctx.window = ctx;
vm.runInNewContext(scriptSrc, ctx);

const result = {
  sidebar2d: sidebarSpan2d.textContent,
  sidebar5h: sidebarSpan5h.textContent,
  sidebarAgo: sidebarSpanAgo.textContent,
  ui2D: uiSpan2D.textContent,
  ui3D: uiSpan3D.textContent,
  ui1M: uiSpan1M.textContent,
  ui2H: uiSpan2H.textContent,
  ui5S: uiSpan5S.textContent,
  uiWorking: uiSpanWorking.textContent,
  uiWorkDir: uiSpanWorkDir.textContent,
  uiThought: uiSpanThought.textContent,
  uiBtnSave: uiBtnSave.textContent,
  uiTextInputVal: uiTextInput.value,
  uiTextInputPh: uiTextInput.placeholder,
  uiTextareaPh: uiTextarea.placeholder,
  uiTextareaTxt: uiTextarea.textContent,
  proseP: proseP.textContent,
  proseTd: proseTd.textContent,
  proseStrong: proseStrong.textContent,
  proseWorking: proseWorking.textContent,
  userText: userText.textContent,
  userErr: userErr.textContent,
  plainTd5h: plainTd5h.textContent,
  plainTdBool: plainTdBool.textContent,
  agy5h: agy5h.textContent,
};
console.log(JSON.stringify(result));
"""
        with tempfile.TemporaryDirectory() as td:
            js_file = Path(td) / "loc.js"
            harness_file = Path(td) / "harness.cjs"
            js_file.write_text(Patcher.DOM_TRANSLATOR_INJECTION, encoding="utf-8")
            harness_file.write_text(harness, encoding="utf-8")
            proc = subprocess.run(
                [node_exe, str(harness_file), str(js_file)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            res = json.loads(proc.stdout.strip())

        # UI chrome relative time & labels still translate
        self.assertEqual(res["sidebar2d"], "2天前")
        self.assertEqual(res["sidebar5h"], "5小时前")
        self.assertEqual(res["sidebarAgo"], "3天前")
        self.assertEqual(res["uiWorking"], "运行中...")
        self.assertEqual(res["uiWorkDir"], "Working directory")
        self.assertEqual(res["uiThought"], "思考耗时 5秒")
        self.assertEqual(res["uiBtnSave"], "保存")

        # Uppercase 2D/3D/1M/2H/5S are never corrupted anywhere
        self.assertEqual(res["ui2D"], "2D")
        self.assertEqual(res["ui3D"], "3D")
        self.assertEqual(res["ui1M"], "1M")
        self.assertEqual(res["ui2H"], "2H")
        self.assertEqual(res["ui5S"], "5S")

        # Input/textarea placeholders translate, but user-typed text/value never mutates
        self.assertEqual(res["uiTextInputVal"], "error")
        self.assertEqual(res["uiTextInputPh"], "搜索")
        self.assertEqual(res["uiTextareaPh"], "搜索")
        self.assertEqual(res["uiTextareaTxt"], "2d")

        # Chat markdown replies, user messages, plain tables, and AGY monitor are untouched
        self.assertEqual(res["proseP"], "2D")
        self.assertEqual(res["proseTd"], "true")
        self.assertEqual(res["proseStrong"], "2d")
        self.assertEqual(res["proseWorking"], "Working...")
        self.assertEqual(res["userText"], "3D")
        self.assertEqual(res["userErr"], "error")
        self.assertEqual(res["plainTd5h"], "5h")
        self.assertEqual(res["plainTdBool"], "false")
        self.assertEqual(res["agy5h"], "5h")


if __name__ == "__main__":
    unittest.main()
