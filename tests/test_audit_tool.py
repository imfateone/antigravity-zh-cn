"""Unit tests for the offline localization audit and UI candidate extractor tools."""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_DIR / "tools"
RENDERER_DIR = REPO_DIR / "antigravity_localization" / "renderer"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import audit_localization  # noqa: E402


class LocalizationAuditToolTests(unittest.TestCase):
    def test_extract_embedded_bundle_with_prefix_and_signature_tail(self):
        payload = b'E.createElement("div",{"data-testid":"overview-panel"},"Overview");'
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("assets/logo.svg", b"<svg/>")
            zf.writestr("main.js", payload)
        synthetic_exe = b"MZ_FAKE_PE_HEADER" + b"\x00" * 128 + zip_buf.getvalue() + b"AUTHENTICODE_TAIL_BYTES"

        with tempfile.TemporaryDirectory() as tmp:
            exe_path = Path(tmp) / "language_server.exe"
            exe_path.write_bytes(synthetic_exe)
            extracted, meta = audit_localization.extract_embedded_bundle(exe_path, "main.js")
            self.assertEqual(extracted, payload)
            self.assertEqual(meta["bundle_size"], len(payload))
            self.assertEqual(meta["zip_entries"], 2)

    def test_extract_ui_candidates_and_audit_pipeline(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")

        synthetic_bundle = r'''
"use strict";
const re = /"FakeRegexString"/gi;
const tpl = `Hello ${cond ? "TemplateInner" : "Other"} world`;
function Overview({ status, count }) {
  return E.createElement(
    "div",
    { className: "flex items-center gap-2", "data-testid": "overview-panel", role: "menu" },
    E.createElement("span", null, "Overview"),
    E.createElement(
      "button",
      { "data-testid": "overview-panel-row-review", "aria-label": "Brand new action" },
      status === "Settings" ? "Review" : "Reload"
    ),
    E.createElement(Modal, { "data-testid": "synthetic-unrouted-modal" }, "Cancel", "Uncatalogued panel label"),
    E.createElement(CommandBox, {
      dataTestId: "command-palette",
      placeholder: "Search for commands...",
      label: `Ignored dynamic`,
      tooltip: "Worked for 12s",
    }),
    E.createElement("span", null, "Background Tasks (7)"),
    helperCall("NonRenderedArgString"),
    "flex grid items-center gap-2 text-sm"
  );
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            bundle_file = Path(tmp) / "main.js"
            bundle_file.write_text(synthetic_bundle, encoding="utf-8")

            proc = subprocess.run(
                [node, str(TOOLS_DIR / "extract_ui_candidates.cjs"), str(bundle_file), str(RENDERER_DIR)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            data = json.loads(proc.stdout)

            self.assertIn("overview-panel", data["testids"])
            self.assertIn("overview-panel-row-review", data["testids"])
            self.assertIn("command-palette", data["testids"])
            self.assertIn("menu", data["testids"]["overview-panel"]["roles"])

            matched_map = {item["text"]: item for item in data["candidates"]["matched_items"]}
            unmatched_map = {item["text"]: item for item in data["candidates"]["items"]}

            self.assertIn("Overview", matched_map)
            self.assertEqual(matched_map["Overview"]["status"], "matched_exact")
            self.assertIn("overview-panel", matched_map["Overview"]["contexts"])

            self.assertIn("Review", matched_map)
            self.assertIn("overview-panel-row-review", matched_map["Review"]["contexts"])

            self.assertIn("Search for commands...", matched_map)
            self.assertIn("command-palette", matched_map["Search for commands..."]["contexts"])

            self.assertIn("Worked for 12s", matched_map)
            self.assertEqual(matched_map["Worked for 12s"]["status"], "matched_formatter")

            self.assertIn("Reload", matched_map)
            self.assertEqual(matched_map["Reload"]["status"], "matched_exact")
            self.assertIn("Background Tasks (7)", matched_map)
            self.assertEqual(matched_map["Background Tasks (7)"]["status"], "matched_formatter")
            self.assertIn("Brand new action", unmatched_map)
            self.assertIn("Uncatalogued panel label", unmatched_map)

            # Regex literals, comparison values, helper calls, and CSS classes must be excluded
            all_texts = set(matched_map) | set(unmatched_map)
            for excluded in ("FakeRegexString", "Settings", "NonRenderedArgString", "flex grid items-center gap-2 text-sm"):
                self.assertNotIn(excluded, all_texts)

            audit = audit_localization.run_audit(bundle_path=bundle_file, app_dir=tmp)
            unrouted_texts = {item["text"] for item in audit["candidates"]["matched_in_unrouted_contexts"]}
            self.assertIn("Cancel", unrouted_texts)
            self.assertNotIn("Overview", unrouted_texts)
            self.assertNotIn("Review", unrouted_texts)

            md = audit_localization.render_markdown_report(audit, top=20)
            self.assertIn("Antigravity 2.34.0 本地化离线审计报告", md)
            self.assertIn("Overview", md)

    def test_diff_audits(self):
        old_a = {
            "testids": {"a": {}, "b": {}},
            "candidates": {"items": [{"text": "Old Missing"}, {"text": "Kept Missing"}]},
            "native_anchors": [],
        }
        new_a = {
            "testids": {"b": {}, "c": {}},
            "candidates": {"items": [{"text": "Kept Missing"}, {"text": "New Missing"}]},
            "native_anchors": [{"file": "dist/tray.js", "anchor": "'Quit'", "status": "drifted"}],
        }
        diff = audit_localization.diff_audits(old_a, new_a)
        self.assertEqual(diff["added_testids"], ["c"])
        self.assertEqual(diff["removed_testids"], ["a"])
        self.assertEqual(diff["added_unmatched"], ["New Missing"])
        self.assertEqual(diff["resolved_unmatched"], ["Old Missing"])
        self.assertEqual(len(diff["drifted_native_anchors"]), 1)

        md = audit_localization.render_markdown_report(
            {
                "bundle_meta": {
                    "member": "main.js",
                    "bundle_size": 100,
                    "bundle_sha256_prefix": "abc",
                    "zip_start_hex": None,
                    "zip_end_hex": None,
                    "zip_entries": 1,
                },
                "catalog_stats": {"dictionary": 10, "core_words": 2, "extra_labels": 3},
                "testid_stats": {
                    "total_unique": 2,
                    "dom_unique": 2,
                    "component_unique": 0,
                    "shell_whitelist_count": 1,
                    "dom_referenced_count": 1,
                    "routed_in_bundle_count": 1,
                    "stale_routed_testids": [],
                },
                "testids": new_a["testids"],
                "candidates": {
                    "total_unique": 2,
                    "matched_exact": 0,
                    "matched_formatter": 0,
                    "unmatched_count": 2,
                    "items": [{"text": "New Missing", "count": 1, "fields": ["text"], "contexts": {"c": 1}}],
                    "matched_in_unrouted_contexts": [],
                },
                "regions": {},
                "native_anchors": new_a["native_anchors"],
            },
            top=10,
            diff=diff,
        )
        self.assertIn("版本间差异对比", md)
        self.assertIn("drifted", md)

    def test_audit_native_anchors_expected_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            dist = app_dir / "resources" / "app" / "dist"
            dist.mkdir(parents=True)
            (dist / "menu.js").write_text(
                "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);\n"
                "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);\n"
                "const viewMenuItem = appMenu.items?.find((item) => item.label === 'View');\n",
                encoding="utf-8",
            )
            (dist / "tray.js").write_text("empty", encoding="utf-8")

            results = {r["anchor"]: r for r in audit_localization.audit_native_anchors(app_dir)}
            sub_anchor = "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);"
            view_anchor = "const viewMenuItem = appMenu.items?.find((item) => item.label === 'View');"
            act_anchor = "const action = updater_1.updateActions[menuItem.label];"
            upd_anchor = "        if (item) {\n            item.label = step;\n            item.enabled = exports.updateActions[step] !== undefined;\n        }"
            self.assertEqual(results[sub_anchor]["status"], "unexpected_count")
            self.assertEqual(results[sub_anchor]["occurrences"], 2)
            self.assertEqual(results[view_anchor]["status"], "ok")
            self.assertEqual(results[act_anchor]["status"], "drifted")
            self.assertEqual(results[upd_anchor]["status"], "missing_file")

    def test_parse_dom_routing_and_detail_template_resolution(self):
        routing = audit_localization.parse_dom_routing(RENDERER_DIR / "antigravity_dom.js")
        self.assertNotIn("palette-sort-last_updated", routing["shell_testids"])
        self.assertNotIn("composer-connectors-submenu", routing["shell_testids"])
        self.assertIn("palette-sort-last_updated", routing["all_referenced_testids"])
        self.assertIn("composer-connectors-submenu", routing["all_referenced_testids"])
        self.assertIn("permissions-menu", routing["all_referenced_testids"])

        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "main.js"
            bundle.write_text(
                'E.createElement("div",{"data-testid":`${a}-detail`});'
                'E.createElement("button",{"data-testid":"overview-panel-row-review"},"Review");',
                encoding="utf-8",
            )
            audit = audit_localization.run_audit(bundle_path=bundle, app_dir=tmp)
            self.assertNotIn("overview-panel-row-review-detail", audit["testid_stats"]["stale_routed_testids"])


if __name__ == "__main__":
    unittest.main()
