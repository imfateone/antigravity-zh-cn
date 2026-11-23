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
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
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

            # Existing installs must replace the previous renderer, even without an official update.
            preload = res_dir / "app" / "dist" / "preload.js"
            preload.write_text(
                "console.log('preload');\n// Antigravity Chinese Localization Engine\nlegacyRenderer();\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"ANTIGRAVITY_APP_DIR": str(app_dir)}), \
                 mock.patch.object(Patcher, "stop_antigravity_desktop_processes", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "ensure_desktop_shortcut", lambda *a, **kw: None), \
                 mock.patch.object(Patcher, "cleanup_stale_updater_cache", lambda *a, **kw: []):
                self.assertTrue(Patcher.apply_patch(relaunch=False))
            localized_preload = preload.read_text(encoding="utf-8")
            self.assertEqual(localized_preload.count("// Antigravity Chinese Localization Engine"), 1)
            self.assertNotIn("legacyRenderer", localized_preload)
            self.assertIn(Patcher.DOM_TRANSLATOR_INJECTION, localized_preload)

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

    def test_dictionary_has_no_duplicate_keys_and_safe_dom_invariants(self):
        """静态守卫：词典无重名覆盖，且注入脚本不含 innerHTML / .value 写入、dead shadowRoot 或全树 characterData。"""
        import re

        js = Patcher.DOM_TRANSLATOR_INJECTION
        m = re.search(r"const dictionary = \{(.*?)\n\};", js, re.S)
        self.assertIsNotNone(m, "dictionary block missing")
        seen: dict[str, str] = {}
        dups: list[str] = []
        for km in re.finditer(r'"((?:\\.|[^"\\])*)"\s*:\s*"((?:\\.|[^"\\])*)"', m.group(1)):
            k = km.group(1)
            if k in seen:
                dups.append(k)
            seen[k] = km.group(2)
        self.assertEqual(dups, [], f"Duplicate dictionary keys found: {dups}")
        self.assertGreater(len(seen), 1500)

        # Hard architectural invariants from Codex P0/P1/P2 review
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("checkEmptyContainer", js)
        self.assertNotIn("node.value =", js)
        self.assertNotIn("node.shadowRoot", js)
        self.assertIn("new Map(Object.entries(dictionary))", js)
        self.assertIn("'data-title'", js)
        # bodyObserver must NOT observe characterData on document.body
        body_obs_match = re.search(r"bodyObserver\.observe\(document\.body,\s*\{(.*?)\}\)", js, re.S)
        self.assertIsNotNone(body_obs_match)
        self.assertNotIn("characterData", body_obs_match.group(1))

    def test_formatter_module_in_node(self):
        import shutil
        import subprocess

        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        subprocess.run(
            [node, str(FIXTURES_DIR / "formatters.cjs"),
             str(REPO_DIR / "antigravity_localization" / "renderer")],
            check=True,
        )

    @staticmethod
    def _find_chromium_exe() -> str | None:
        import shutil

        candidates = [
            shutil.which("chrome"),
            shutil.which("chromium"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
        return None

    def _run_in_headless_chromium(self, html_content: str) -> dict:
        import shutil
        import subprocess

        node_exe = shutil.which("node")
        chrome_exe = self._find_chromium_exe()
        if not node_exe or not chrome_exe:
            self.skipTest("node or headless Chromium not installed")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ud = root / "profile"
            js_file = root / "loc.js"
            html_file = root / "page.html"
            runner_file = FIXTURES_DIR / "chromium_runner.cjs"
            js_file.write_text(Patcher.DOM_TRANSLATOR_INJECTION, encoding="utf-8")
            html_contents = html_content.replace("__LOC_JS_URL__", js_file.as_uri())
            fixture_script = FIXTURES_DIR / "antigravity_dom_fixture.js"
            html_contents = html_contents.replace("__FIXTURE_JS_URL__", fixture_script.as_uri())
            html_file.write_text(html_contents, encoding="utf-8")
            proc = subprocess.run(
                [node_exe, str(runner_file), chrome_exe, html_file.as_uri(), str(ud)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=35,
            )
            if proc.returncode != 0:
                self.fail(f"Chromium runner failed (rc={proc.returncode}): {proc.stderr}")
            data = json.loads(proc.stdout.strip())
            if "__error" in data:
                self.fail(f"Browser test threw error: {data['__error']}")
            return data

    def test_chromium_p0_p1_p2_full_regression(self):
        """真实无头 Chromium 浏览器全量回归：覆盖 Codex 全部 P0/P1/P2 复现与正向 UI 槽位。"""
        html = (FIXTURES_DIR / "localization.html").read_text(encoding="utf-8")

        res = self._run_in_headless_chromium(html)

        # App shell & Settings positive localization
        self.assertEqual(res["sb2d"], "2天前")
        self.assertEqual(res["sb5h"], "5小时前")
        self.assertEqual(res["sbAgo"], "3天前")
        self.assertEqual(res["sb2D"], "2D")
        self.assertEqual(res["sb3D"], "3D")
        self.assertEqual(res["sbEmpty"], "暂无项目")
        self.assertEqual(res["sidebarAction"], "新建对话")
        self.assertEqual(res["sidebarUserTitle"], "Open")
        self.assertEqual(res["sidebarUserTooltip"], "Open")
        self.assertEqual(res["sidebarCustomName"], "Editing app.py")
        self.assertEqual(res["titlebarAction"], "打开")
        self.assertEqual(res["titlebarUserTitle"], "Settings")
        self.assertEqual(res["titlebarUserTooltip"], "Settings")
        self.assertTrue(res["origEmptySvgConnected"])
        self.assertEqual(res["setH2"], "设置")
        self.assertEqual(res["setP"], "管理您的系统与声音通知偏好")
        self.assertEqual(res["setTh"], "操作")
        self.assertEqual(res["setTdOpen"], "打开设置")
        self.assertEqual(res["setTd2d"], "2d")

        # P0 destructive rules & P1 prototype pollution
        self.assertEqual(res["diagSee"], "See our server response: custom trace.")
        self.assertEqual(res["diagPatch"], "Patch note: No projects found in the log.")
        self.assertEqual(res["diagReq"], "It requires Node 20 to be installed.")
        self.assertEqual(res["diagThought"], "Thought for a while testing")
        self.assertEqual(res["diagWorked"], "Worked for fun")
        self.assertEqual(res["diagPrefixTrunc"], "Confirming this undo action will make the following changes: custom trace must stay.")
        self.assertEqual(res["diagSettingsTrunc"], "Manage your notification preferences: custom note must stay.")
        self.assertEqual(res["diagEllipsisTrunc"], "Manage your notification preferences only in this workspace…")
        self.assertEqual(res["diagGeminiLong"], "Gemini 4 Argon is now available in preview with custom quota details.")
        self.assertEqual(res["proto1"], "__proto__")
        self.assertEqual(res["proto2"], "hasOwnProperty")
        self.assertEqual(res["proto3"], "constructor")
        self.assertEqual(res["afterProto"], "设置")

        # P0 editable, checkEmptyContainer deletion & NotFoundError
        self.assertEqual(res["cePlain"], "Settings")
        self.assertEqual(res["ceProseText"], "Open")
        self.assertEqual(res["ceProseAria"], "Search")
        self.assertEqual(res["proseEmpty"], "No projects found")
        self.assertTrue(res["draftConnected"])
        self.assertEqual(res["draftVal"], "my draft")
        self.assertEqual(res["draftPh"], "搜索")
        self.assertTrue(res["removeChildOk"])

        # P0 role="button" preview protection (marked + unmarked)
        self.assertEqual(res["previewTd"], "Settings")
        self.assertEqual(res["previewBq"], "Open")
        self.assertEqual(res["previewP"], "Save")
        self.assertEqual(res["previewSpan"], "Review")
        self.assertEqual(res["unmarkedPreviewH1"], "Open")
        self.assertEqual(res["unmarkedPreviewP"], "Settings")

        # P0/P2 independent data-tooltip vs data-title & fault isolation
        self.assertEqual(res["tipTooltip"], "设置")
        self.assertEqual(res["tipInitialDataTitle"], "Custom Keep")
        self.assertEqual(res["tipUpdatedDataTitle"], "打开")
        self.assertEqual(res["tipText"], "保存")
        self.assertEqual(res["faultGoodBtn"], "运行耗时 42秒")

        # P0 form submission values preserved (ALL native <option> untouched, even after removing value!)
        self.assertEqual(res["formIntent"], "delete")
        self.assertEqual(res["formBtnText"], "删除")
        self.assertEqual(res["formInputVal"], "Save")
        self.assertEqual(res["optImplicitText"], "Open")
        self.assertEqual(res["formSelectMode"], "Close")
        self.assertEqual(res["optNestedMode"], "Open")
        self.assertEqual(res["optNestedSpanText"], "Open")
        self.assertEqual(res["optExplicitText"], "Close")
        self.assertEqual(res["optExplicitVal"], "Close")

        # P1 positive UI slots inside chat & dynamic Composer button & unreset prose restoration
        self.assertEqual(res["btnWorked"], "运行耗时 22秒")
        self.assertEqual(res["migratedText"], "Worked for 99s")
        self.assertEqual(res["unresetInitial"], "运行耗时 7秒")
        self.assertEqual(res["unresetProseText"], "Worked for 7s")
        self.assertEqual(res["btnThought"], "思考耗时 1分 5秒 >")
        self.assertEqual(res["btnThoughtLate"], "思考耗时 8秒")
        self.assertEqual(res["btnExplored"], "已浏览 2 个文件")
        self.assertEqual(res["btnEditing"], "正在编辑 foo$&bar.py +3 -1")
        self.assertEqual(res["sumSingle"], "2 个文件已修改 +99 -23 >")
        self.assertEqual(res["sumReview1"], "审阅")
        self.assertEqual(res["sumSplitLbl"], "2 个文件已修改")
        self.assertEqual(res["sumSplitAdd"], "+99")
        self.assertEqual(res["sumSplitDel"], "-23")
        self.assertEqual(res["sumReview2"], "审阅")
        self.assertEqual(res["dlgTitle"], "允许写入此路径吗？")
        self.assertEqual(res["dlgCode"], "/tmp/Settings")
        self.assertEqual(res["dlgDiag"], "See our server response: custom trace.")
        self.assertEqual(res["dlgAllow"], "是，仅本次允许")
        self.assertEqual(res["confirmTitle"], "确认撤销")
        self.assertEqual(res["confirmInfo"], "确认此撤销操作将做出以下更改：")
        self.assertEqual(res["confirmPath"], "Review")
        self.assertEqual(res["confirmButton"], "确认")
        self.assertEqual(res["fbCopy"], "复制")
        self.assertEqual(res["fbGood"], "好的回答")
        self.assertEqual(res["fbBad"], "差的回答")
        self.assertEqual(res["agyTurnPill"], "用量 1.9M tok")
        self.assertEqual(res["tsInitial"], "刚刚")
        self.assertEqual(res["tsUpdated"], "2分钟前")
        self.assertEqual(res["compPh"], "搜索")
        self.assertEqual(res["compOverlay"], "输入任何问题，使用 @ 提及")
        self.assertEqual(res["compLexical"], "Settings")
        self.assertEqual(res["compVal"], "draft")
        self.assertEqual(res["compSend"], "发送")
        self.assertEqual(res["compSendUpdated"], "停止")

        # P0 bare unclassed AI reply & Round-2 prose slot bypasses all zero-write
        self.assertEqual(res["userMsg"], "Settings")
        self.assertEqual(res["bareSettings"], "Settings")
        self.assertEqual(res["bare2m"], "2m")
        self.assertEqual(res["bareFalse"], "false")
        self.assertEqual(res["bareJustNow"], "Just now")
        self.assertEqual(res["bare3dAgo"], "3d ago")
        self.assertEqual(res["bareWorking"], "Working...")
        self.assertEqual(res["bareReview"], "Review")
        self.assertEqual(res["bareEmpty"], "No projects found")
        self.assertEqual(res["bareSummaryProse"], "2 files changed +99 -23 >")
        self.assertEqual(res["bareDirectHost"], "Settings")
        self.assertEqual(res["prosePBtnText"], "Review")
        self.assertEqual(res["prosePBtnAria"], "Settings")
        self.assertEqual(res["proseHdrSettings"], "Settings")
        self.assertEqual(res["proseHdrReview"], "Review")
        self.assertEqual(res["proseDlgSettings"], "Settings")
        self.assertEqual(res["proseDlgReview"], "Review")
        self.assertEqual(res["proseDlgTrunc"], "Confirming this undo action will make the following changes: custom trace must stay.")
        self.assertEqual(res["proseFakeFbBtnText"], "Good response")
        self.assertEqual(res["proseFakeFbBtnAria"], "Good response")
        self.assertEqual(res["proseFakeFbTs"], "2m")
        self.assertEqual(res["proseFakeSumLbl"], "2 files changed")
        self.assertEqual(res["proseFakeSumBtn"], "Review")
        self.assertEqual(res["bareRoleBtnReview"], "Review")

        # P0 virtual unmount, deep nesting, empty chat w/ nav, history w/ aside + new turn, portals, artifact & migration
        self.assertEqual(res["virtDeepP"], "Review")
        self.assertEqual(res["virtDeepBare"], "Open")
        self.assertEqual(res["virtNewDiv"], "Settings")
        self.assertEqual(res["virtNewSpan"], "2m")
        self.assertEqual(res["emptyChatSettings"], "Settings")
        self.assertEqual(res["emptyChat2m"], "2m")
        self.assertEqual(res["histAiSettings"], "Settings")
        self.assertEqual(res["histNewTurn"], "Settings")
        self.assertEqual(res["tpSettings"], "Settings")
        self.assertEqual(res["tp2m"], "2m")
        self.assertEqual(res["lateTpSettings"], "Settings")
        self.assertEqual(res["lateTp2m"], "2m")
        self.assertEqual(res["lateTpAfterUnmount"], "Settings")
        self.assertEqual(res["raceTpSettings"], "Settings")
        self.assertEqual(res["raceTpTitle"], "Settings")
        self.assertEqual(res["raceTp2m"], "2m")
        self.assertEqual(res["raceBtnText"], "思考耗时 9秒")
        self.assertEqual(res["artH1"], "Settings")
        self.assertEqual(res["artBody"], "Open")
        self.assertEqual(res["artContentBtn"], "Review")
        self.assertEqual(res["artUnmarkedPreview"], "Review")
        self.assertEqual(res["artClose"], "关闭")
        self.assertEqual(res["dynArtH1"], "Settings")
        self.assertEqual(res["iframeText"], "Settings")
        self.assertEqual(res["relocCompProse"], "Settings")
        self.assertEqual(res["detachedText"], "Settings")

    def test_chromium_content_ownership_and_node_reuse(self):
        html = (FIXTURES_DIR / "ownership.html").read_text(encoding="utf-8")
        self.assertEqual(self._run_in_headless_chromium(html)["contentWrites"], 0)

    def test_chromium_mutation_races(self):
        html = (FIXTURES_DIR / "mutation_races.html").read_text(encoding="utf-8")
        result = self._run_in_headless_chromium(html)
        self.assertEqual(result.pop("migratedTextRecords"), 0, result)
        for scenario, passed in result.items():
            with self.subTest(scenario=scenario):
                self.assertTrue(passed)

    def test_chromium_portal_history_before_display_writes(self):
        html = (FIXTURES_DIR / "portal_history.html").read_text(encoding="utf-8")
        result = self._run_in_headless_chromium(html)
        self.assertTrue(result["engineCallbackWasHeld"])
        self.assertTrue(result["earlierShadowsTrailing"])
        self.assertTrue(result["crossedFrame"])
        self.assertTrue(result["mutationDuringSettlement"])
        self.assertEqual(result["removedSubtreeScans"], 1)
        ordinary_ui = {
            "control_fake_outside_chat_localized",
            "control_new_earlier_duplicate",
            "control_id_reused_after_both_removed",
            "control_new_earlier_for_preexisting",
        }
        self.assertTrue(ordinary_ui.issubset(result["cases"]))
        for scenario, state in result["cases"].items():
            with self.subTest(scenario=scenario):
                translated = scenario in ordinary_ui
                expected = "设置" if translated else "Settings"
                self.assertEqual(state["text"], expected)
                self.assertEqual(state["title"], expected)
                self.assertEqual(state["writes"], 2 if translated else 0)

    def test_chromium_streaming_performance_benchmark(self):
        """真实无头 Chromium 性能与生命周期回归：原位流式、结构化流式、迁移解绑、2000 按钮批量挂载与重插复绑。"""
        html = (FIXTURES_DIR / "streaming.html").read_text(encoding="utf-8")

        res = self._run_in_headless_chromium(html)
        for key in ("turns2000", "spans2000"):
            m = res[key]
            self.assertEqual(m["totalRecords"], 0, f"{key} received prose MutationRecords: {m}")
            self.assertEqual(m["totalCbCalls"], 0, f"{key} invoked observer callbacks: {m}")
            self.assertEqual(m["totalQsCalls"], 0, f"{key} executed querySelector during streaming: {m}")
            self.assertEqual(m["finalText"], "No projects found", f"{key} mutated prose text: {m}")
            self.assertLess(m["medianCbMs"], 2.0, f"{key} exceeded 2ms budget: {m}")

        # Structured streaming (including inside chat role="dialog"!): 0 querySelector calls and 0 prose writes!
        for key in ("structTurns", "structSpans", "structChatDialog", "structChatMenu"):
            self.assertEqual(res[key]["qsCalls"], 0, f"{key} ran querySelector on structured prose: {res[key]}")
            self.assertTrue(res[key]["untouched"], f"{key} mutated structured prose: {res[key]}")

        # Migrated Text into .prose (both single node and >520-sibling subtree): 0 characterData records!
        self.assertEqual(res["migratedBench"]["charDataRecords"], 0, res["migratedBench"])
        self.assertEqual(res["migratedBench"]["finalText"], "Worked for 119s")
        self.assertEqual(res["bigMigratedBench"]["restored"], "Worked for 17s", res["bigMigratedBench"])
        self.assertEqual(res["bigMigratedBench"]["charDataRecords"], 0, res["bigMigratedBench"])
        self.assertEqual(res["bigMigratedBench"]["finalText"], "Worked for 119s")

        # 2,000-slot mount: zero disconnect storm, linear observe count, no 1s long task, detached button re-binds!
        b = res["bulk2000"]
        self.assertEqual(b["firstMount"], {"disconnects": 0, "observations": 2000}, b)
        self.assertEqual(b["reorder"], {"disconnects": 0, "observations": 0, "writes": 0}, b)
        self.assertEqual(b["remount"]["disconnects"], 2000, b)
        self.assertEqual(b["remount"]["observations"], 2000, b)
        self.assertTrue(b["remount"]["all2000Restored"], b)
        self.assertTrue(b["remount"]["all2000Rebound"], b)
        self.assertLess(b["maxRafMs"], 40.0, f"long task regressed: {b}")
        self.assertTrue(b["all2000Translated"], f"not all 2000 buttons translated: {b}")
        self.assertEqual(b["reinsertedBtnText"], "运行耗时 99秒", f"re-inserted button failed to re-bind: {b}")

    def test_chromium_startup_2000_buttons_no_long_task(self):
        """真实无头 Chromium 启动性能回归：页面初始已有 2,000 个按钮时分帧初始化，不产生 Long Task。"""
        html = (FIXTURES_DIR / "startup.html").read_text(encoding="utf-8")

        for scenario, expected_count in (("steady", 2000), ("remove-once", 1999)):
            with self.subTest(scenario=scenario):
                res = self._run_in_headless_chromium(html.replace("__STARTUP_SCENARIO__", scenario))
                self.assertEqual(res["buttonCount"], expected_count, res)
                self.assertTrue(res["allTranslated"], res)
                self.assertTrue(res["tailTranslated"], res)
                self.assertTrue(res["reportsLongTasks"], "Chromium did not support Long Task instrumentation")
                self.assertLess(res["dclBootMs"], 30.0, res)
                self.assertLess(res["maxRafMs"], 30.0, res)
                self.assertEqual(res["longTasks"], [], res)


if __name__ == "__main__":
    unittest.main()
