"""离线本地化审计与 UI 候选文案提取工具（纯只读，不改动客户端安装）。"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

TOOLS_DIR = Path(__file__).resolve().parent
REPO_DIR = TOOLS_DIR.parent
RENDERER_DIR = REPO_DIR / "antigravity_localization" / "renderer"
PATCHER_PATH = REPO_DIR / "Antigravity-Patcher.py"

if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from _ag_common import find_app_dir  # noqa: E402

NATIVE_ANCHORS: list[tuple[str, str, int]] = [
    ("dist/menu.js", "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);", 1),
    ("dist/menu.js", "const viewMenuItem = appMenu.items?.find((item) => item.label === 'View');", 1),
    ("dist/menu.js", "const action = updater_1.updateActions[menuItem.label];", 1),
    (
        "dist/updater.js",
        "        if (item) {\n            item.label = step;\n            item.enabled = exports.updateActions[step] !== undefined;\n        }",
        1,
    ),
    (
        "dist/tray.js",
        "(count > 0 ? `${count}` : 'No') +\n                    ' agent' +\n                    (count === 1 ? '' : 's') +\n                    ' running'",
        1,
    ),
    ("dist/main.js", "label: 'No agents running'", 1),
    ("dist/main.js", "label: `Open ${electron_1.app.getName()}`", 1),
    ("dist/main.js", "label: 'Quit'", 1),
    ("dist/main.js", "buttons: ['Cancel', 'Quit']", 1),
    ("dist/main.js", "title: 'Confirm Quit'", 1),
    ("dist/main.js", "message: 'Are you sure you want to quit?'", 1),
    ("dist/main.js", "detail: 'There may be agents or background tasks running.'", 1),
    ("dist/provisionSplash.js", "Setting up WSL: ", 1),
]

_REGION_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Overview", re.compile(r"(overview|battle-overview)", re.I)),
    ("Command Palette", re.compile(r"(command[-_]?palette|quick[-_]?open)", re.I)),
    ("Files / File Tree", re.compile(r"(file[-_]?tree|workspace[-_]?file|changed[-_]?files|\bfiles\b)", re.I)),
    ("Review / Diff", re.compile(r"(review|diff|hunk|patch)", re.I)),
    ("Terminal / Background Tasks", re.compile(r"(terminal|background[-_]?task|running[-_]?items|pty)", re.I)),
    (
        "Settings",
        re.compile(
            r"(settings|shortcut|keybinding|voice|account|remote[-_]?control|appearance|notification)",
            re.I,
        ),
    ),
    ("Automations / Sidecars", re.compile(r"(automation|sidecar|schedule|cron)", re.I)),
    (
        "Plugins / Marketplace / Customizations",
        re.compile(r"(plugin|marketplace|customization|mcp|skill|workflow|hook|rule)", re.I),
    ),
    ("Browser", re.compile(r"(browser|webview|url[-_]?bar)", re.I)),
    (
        "Composer / Model / Permissions",
        re.compile(
            r"(composer|agent[-_]?input|model[-_]?selector|orchestrator|permission|cascade|worked[-_]?for|thinking|progress[-_]?updates|tool[-_]?group|inline[-_]?permission)",
            re.I,
        ),
    ),
    ("Artifact", re.compile(r"artifact", re.I)),
    (
        "Sidebar / Conversations / Projects",
        re.compile(r"(sidebar|conversation|project|history|pinned|archive|home[-_]?greeting)", re.I),
    ),
    (
        "Overlays (Dialog / Popover / Menu / Select / Tooltip / Toast)",
        re.compile(r"(dialog|modal|popover|dropdown|menu|select|tooltip|toast|banner|combobox|popup)", re.I),
    ),
]


def classify_ui_region(label: str) -> str:
    if not label or label == "<root>":
        return "Other"
    for region, pat in _REGION_RULES:
        if pat.search(label):
            return region
    return "Other"


def extract_embedded_bundle(
    binary_path: str | Path,
    member_name: str = "main.js",
) -> tuple[bytes, dict]:
    bin_path = Path(binary_path)
    data = bin_path.read_bytes()
    pos = len(data)
    while True:
        eocd = data.rfind(b"PK\x05\x06", 0, pos)
        if eocd == -1:
            break
        if eocd + 22 <= len(data):
            _disk, _cd_disk, _n_disk, _n_total, cd_size, cd_off, cmt_len = struct.unpack_from(
                "<HHHHIIH", data, eocd + 4
            )
            zip_start = eocd - cd_size - cd_off
            zip_end = eocd + 22 + cmt_len
            if (
                zip_start >= 0
                and zip_end <= len(data)
                and data[zip_start : zip_start + 4] in (b"PK\x03\x04", b"PK\x05\x06")
            ):
                try:
                    with zipfile.ZipFile(io.BytesIO(data[zip_start:zip_end])) as zf:
                        if member_name in zf.namelist():
                            bundle_bytes = zf.read(member_name)
                            return bundle_bytes, {
                                "binary_path": str(bin_path),
                                "binary_size": len(data),
                                "zip_start_hex": hex(zip_start),
                                "zip_end_hex": hex(zip_end),
                                "zip_entries": len(zf.namelist()),
                                "member": member_name,
                                "bundle_size": len(bundle_bytes),
                                "bundle_sha256_prefix": hashlib.sha256(bundle_bytes).hexdigest()[:16],
                            }
                except (zipfile.BadZipFile, KeyError, OSError):
                    pass
        pos = eocd
    raise ValueError(f"未在 {bin_path} 中找到包含 {member_name} 的内嵌 ZIP。")


def read_asar_file(asar_path: Path, rel_path: str) -> bytes | None:
    if not asar_path.is_file():
        return None
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p]
    with asar_path.open("rb") as f:
        size_buf = f.read(8)
        if len(size_buf) < 8:
            return None
        _pickle_size, header_size = struct.unpack("<II", size_buf)
        header_buf = f.read(header_size)
        if len(header_buf) < max(8, header_size):
            return None
        _payload_size, json_len = struct.unpack("<II", header_buf[:8])
        if 8 + json_len > len(header_buf):
            return None
        tree = json.loads(header_buf[8 : 8 + json_len].decode("utf-8"))
        node = tree
        for part in parts:
            files_map = node.get("files") if isinstance(node, dict) else None
            if not isinstance(files_map, dict) or part not in files_map:
                return None
            node = files_map[part]
        if not isinstance(node, dict) or "offset" not in node or "size" not in node:
            return None
        offset = int(node["offset"])
        size = int(node["size"])
        f.seek(8 + header_size + offset)
        return f.read(size)


def _read_native_target(app_dir: Path, rel_path: str) -> tuple[str | None, str]:
    resources_dir = (
        app_dir / "Contents" / "Resources"
        if sys.platform == "darwin"
        else app_dir / "resources"
    )
    for asar_name in ("app.asar.disabled", "app.asar"):
        asar_file = resources_dir / asar_name
        raw = read_asar_file(asar_file, rel_path)
        if raw is not None:
            return raw.decode("utf-8", errors="replace").replace("\r\n", "\n"), asar_name
    unpacked = resources_dir / "app" / Path(*rel_path.split("/"))
    if unpacked.is_file():
        return unpacked.read_text(encoding="utf-8", errors="replace"), "resources/app"
    return None, "missing"


def audit_native_anchors(app_dir: str | Path | None) -> list[dict]:
    if not app_dir:
        return []
    app_path = Path(app_dir)
    if not app_path.exists():
        return []
    file_cache: dict[str, tuple[str | None, str]] = {}
    results: list[dict] = []
    for rel_path, anchor, expected_count in NATIVE_ANCHORS:
        if rel_path not in file_cache:
            file_cache[rel_path] = _read_native_target(app_path, rel_path)
        content, source = file_cache[rel_path]
        occ = content.count(anchor) if content is not None else 0
        if content is None:
            status = "missing_file"
        elif occ == 0:
            status = "drifted"
        elif occ != expected_count:
            status = "unexpected_count"
        else:
            status = "ok"
        results.append(
            {
                "file": rel_path,
                "anchor": anchor,
                "expected_count": expected_count,
                "occurrences": occ,
                "source": source,
                "status": status,
            }
        )
    return results


def parse_dom_routing(dom_js_path: Path = RENDERER_DIR / "antigravity_dom.js") -> dict:
    src = dom_js_path.read_text(encoding="utf-8")

    shell_testids: set[str] = set()
    shell_match = re.search(r"const\s+shell\s*=\s*\[([\s\S]*?)\]\.join", src)
    if shell_match:
        shell_testids.update(re.findall(r'data-testid="([^"]+)"', shell_match.group(1)))
    shell_set_match = re.search(r"const\s+SHELL_TESTIDS\s*=\s*new Set\(\[([\s\S]*?)\]\)", src)
    if shell_set_match:
        shell_testids.update(re.findall(r"'([^']+)'", shell_set_match.group(1)))

    all_referenced: set[str] = set(shell_testids)
    all_referenced.update(re.findall(r'data-testid="([^"]+)"', src))
    all_referenced.update(re.findall(r"(?:testId\([^)]+\)|tid)\s*[!=]==\s*'([^']+)'", src))

    for set_name in (
        "HARD_PROTECTED_TESTIDS",
        "SHELL_TESTIDS",
        "SELF_OWNED_MENU_TESTIDS",
        "MENU_SCOPED_TESTIDS",
        "FIXED_MENU_TRIGGER_TESTIDS",
        "HI_MODAL_TESTIDS",
        "CUSTOMIZE_SIDEBAR_FIXED_TESTIDS",
        "OVERVIEW_ROW_TESTIDS",
        "OVERVIEW_AUX_SECTION_TESTIDS",
        "statusIds",
        "permissionButtons",
        "sidebarActions",
        "titlebarActions",
    ):
        m = re.search(rf"const\s+{set_name}\s*=\s*new Set\(\[([\s\S]*?)\]\)", src)
        if m:
            all_referenced.update(re.findall(r"'([^']+)'", m.group(1)))

    return {
        "shell_testids": sorted(shell_testids),
        "all_referenced_testids": sorted(all_referenced),
    }


def _invoke_node_extractor(bundle_path: Path, renderer_dir: Path = RENDERER_DIR) -> dict:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("未检测到 node，请安装 Node.js 后重试。")
    proc = subprocess.run(
        [node, str(TOOLS_DIR / "extract_ui_candidates.cjs"), str(bundle_path), str(renderer_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(proc.stdout)


def run_audit(
    *,
    app_dir: str | Path | None = None,
    language_server_path: str | Path | None = None,
    bundle_path: str | Path | None = None,
    renderer_dir: Path = RENDERER_DIR,
) -> dict:
    detected_app = Path(app_dir) if app_dir else (Path(find_app_dir()) if find_app_dir() else None)
    if bundle_path:
        b_path = Path(bundle_path)
        raw_bytes = b_path.read_bytes()
        bundle_meta = {
            "binary_path": str(b_path),
            "binary_size": len(raw_bytes),
            "zip_start_hex": None,
            "zip_end_hex": None,
            "zip_entries": 1,
            "member": b_path.name,
            "bundle_size": len(raw_bytes),
            "bundle_sha256_prefix": hashlib.sha256(raw_bytes).hexdigest()[:16],
        }
        extracted = _invoke_node_extractor(b_path, renderer_dir=renderer_dir)
    else:
        ls_path = Path(language_server_path) if language_server_path else (
            (detected_app / "Contents" / "Resources" / "bin" / "language_server")
            if sys.platform == "darwin" and detected_app
            else ((detected_app / "resources" / "bin" / "language_server.exe") if detected_app else None)
        )
        if not ls_path or not ls_path.is_file():
            raise FileNotFoundError(f"未找到 language_server 二进制文件: {ls_path}")
        bundle_bytes, bundle_meta = extract_embedded_bundle(ls_path, "main.js")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_bundle = Path(tmp) / "main.js"
            tmp_bundle.write_bytes(bundle_bytes)
            extracted = _invoke_node_extractor(tmp_bundle, renderer_dir=renderer_dir)

    bundle_raw = raw_bytes if bundle_path else bundle_bytes
    bundle_text = bundle_raw.decode("utf-8", errors="replace")
    dom_routing = parse_dom_routing(renderer_dir / "antigravity_dom.js")
    referenced_set = set(dom_routing["all_referenced_testids"])
    shell_set = set(dom_routing["shell_testids"])
    bundle_testids = extracted["testids"]
    bundle_id_set = set(bundle_testids.keys())
    has_detail_template = bool(re.search(r"`\$\{[^}`]+\}-detail`", bundle_text))

    resolved_bundle_ids = set(bundle_id_set)
    if has_detail_template:
        for tid in referenced_set:
            if tid.endswith("-detail") and tid[:-7] in bundle_id_set:
                resolved_bundle_ids.add(tid)

    routed_in_bundle = sorted(referenced_set & resolved_bundle_ids)
    stale_routed = sorted(referenced_set - resolved_bundle_ids)

    region_stats: dict[str, dict] = defaultdict(
        lambda: {
            "total_testids": 0,
            "routed_testids": 0,
            "unmatched_candidates": 0,
            "matched_unrouted_candidates": 0,
            "sample_unrouted_testids": [],
            "top_unmatched": [],
            "top_matched_unrouted": [],
        }
    )

    for tid in sorted(bundle_id_set):
        region = classify_ui_region(tid)
        st = region_stats[region]
        st["total_testids"] += 1
        if tid in referenced_set:
            st["routed_testids"] += 1
        elif len(st["sample_unrouted_testids"]) < 12:
            st["sample_unrouted_testids"].append(tid)

    matched_in_unrouted_contexts: list[dict] = []
    for item in extracted["candidates"].get("matched_items", []):
        ctxs = item.get("contexts") or {}
        unrouted_ctxs = [
            ctx for ctx in ctxs.keys() if ctx != "<root>" and ctx not in referenced_set
        ]
        if unrouted_ctxs:
            matched_in_unrouted_contexts.append(
                {
                    "text": item["text"],
                    "status": item["status"],
                    "count": item["count"],
                    "fields": item["fields"],
                    "unrouted_contexts": unrouted_ctxs,
                }
            )
            primary_region = classify_ui_region(unrouted_ctxs[0])
            st = region_stats[primary_region]
            st["matched_unrouted_candidates"] += 1
            if len(st["top_matched_unrouted"]) < 15:
                st["top_matched_unrouted"].append(
                    {
                        "text": item["text"],
                        "count": item["count"],
                        "contexts": unrouted_ctxs[:4],
                    }
                )

    for item in extracted["candidates"].get("items", []):
        ctxs = list((item.get("contexts") or {}).keys())
        region = classify_ui_region(ctxs[0] if ctxs else "<root>")
        st = region_stats[region]
        st["unmatched_candidates"] += 1
        if len(st["top_unmatched"]) < 15:
            st["top_unmatched"].append(
                {
                    "text": item["text"],
                    "count": item["count"],
                    "fields": item["fields"],
                    "contexts": ctxs[:4],
                }
            )

    native_anchors = audit_native_anchors(detected_app)

    return {
        "bundle_meta": bundle_meta,
        "catalog_stats": extracted["catalog_stats"],
        "testid_stats": {
            **extracted["testid_stats"],
            "shell_whitelist_count": len(shell_set),
            "dom_referenced_count": len(referenced_set),
            "routed_in_bundle_count": len(routed_in_bundle),
            "stale_routed_testids": stale_routed,
        },
        "testids": bundle_testids,
        "candidates": {
            "total_unique": extracted["candidates"]["total_unique"],
            "matched_exact": extracted["candidates"]["matched_exact"],
            "matched_formatter": extracted["candidates"]["matched_formatter"],
            "unmatched_count": extracted["candidates"]["unmatched_count"],
            "items": extracted["candidates"]["items"],
            "matched_in_unrouted_contexts": matched_in_unrouted_contexts,
        },
        "regions": dict(sorted(region_stats.items(), key=lambda kv: (-kv[1]["unmatched_candidates"], kv[0]))),
        "native_anchors": native_anchors,
    }


def diff_audits(old_audit: dict, new_audit: dict) -> dict:
    old_ids = set((old_audit.get("testids") or {}).keys())
    new_ids = set((new_audit.get("testids") or {}).keys())

    old_unmatched = {item["text"] for item in (old_audit.get("candidates") or {}).get("items", [])}
    new_unmatched = {item["text"] for item in (new_audit.get("candidates") or {}).get("items", [])}

    drifted_now = [
        {"file": a["file"], "anchor": a["anchor"]}
        for a in (new_audit.get("native_anchors") or [])
        if a.get("status") in ("drifted", "unexpected_count")
    ]
    return {
        "added_testids": sorted(new_ids - old_ids),
        "removed_testids": sorted(old_ids - new_ids),
        "added_unmatched": sorted(new_unmatched - old_unmatched),
        "resolved_unmatched": sorted(old_unmatched - new_unmatched),
        "drifted_native_anchors": drifted_now,
    }


def _esc_md(val: str) -> str:
    return val.replace("|", "\\|").replace("\r", " ").replace("\n", "\\n")


def render_markdown_report(audit: dict, *, top: int = 150, diff: dict | None = None) -> str:
    meta = audit["bundle_meta"]
    cat = audit["catalog_stats"]
    tstats = audit["testid_stats"]
    cands = audit["candidates"]
    total_c = max(1, cands["total_unique"])
    matched_total = cands["matched_exact"] + cands["matched_formatter"]

    lines: list[str] = [
        "# Antigravity 2.34.0 本地化离线审计报告",
        "",
        "## 一、全局量化总览",
        "",
        "| 指标 | 数值 |",
        "| :--- | :--- |",
        f"| 前端目标 | `{meta['member']}` (`{meta['bundle_size']:,}` 字节，SHA-256 前缀 `{meta['bundle_sha256_prefix']}`) |",
        f"| 内嵌 ZIP 偏移 | `{meta['zip_start_hex']}` – `{meta['zip_end_hex']}`（共 `{meta['zip_entries']}` 个条目） |",
        f"| 词典规模 | 主词典 `{cat['dictionary']}` · 短词表 `{cat['core_words']}` · 额外标签 `{cat['extra_labels']}` |",
        f"| 静态 `data-testid` / `testId` | 共 `{tstats['total_unique']}` 个（DOM `data-testid`: `{tstats['dom_unique']}`，组件 prop: `{tstats['component_unique']}`） |",
        f"| `antigravity_dom.js` 路由引用 | `shell` 直接白名单 `{tstats['shell_whitelist_count']}` 个；全部引用 `{tstats['dom_referenced_count']}` 个；命中当前 bundle `{tstats['routed_in_bundle_count']}` 个 |",
        f"| 静态 UI 英文候选（去重） | 共 `{cands['total_unique']}` 个（精确命中 `{cands['matched_exact']}` · 格式器命中 `{cands['matched_formatter']}` · 合计命中 `{matched_total}` / `{matched_total * 100 / total_c:.1f}%` · 未命中 `{cands['unmatched_count']}`） |",
        "",
    ]

    if tstats["stale_routed_testids"]:
        lines.append(
            f"> [!WARNING]\n> 以下 `{len(tstats['stale_routed_testids'])}` 个在 `antigravity_dom.js` 中引用的 ID 未在当前 bundle 中静态出现：`{', '.join(tstats['stale_routed_testids'][:20])}`"
        )
        lines.append("")

    anchors = audit.get("native_anchors") or []
    if anchors:
        drifted = [a for a in anchors if a["status"] != "ok"]
        lines.extend([
            "## 二、主进程静态替换锚点审计",
            "",
            f"共检查 `{len(anchors)}` 条原生替换规则，其中 `{len(drifted)}` 条在当前版本未命中（`drifted` / 缺失）：",
            "",
            "| 文件 | 来源 | 命中次数 | 状态 | 锚点片段 |",
            "| :--- | :--- | ---: | :--- | :--- |",
        ])
        for a in anchors:
            anchor_text = a.get("anchor", "")
            snippet = _esc_md(anchor_text[:65] + ("..." if len(anchor_text) > 65 else ""))
            lines.append(
                f"| `{a.get('file', '')}` | `{a.get('source', '-')}` | {a.get('occurrences', 0)} | `{a.get('status', 'unknown')}` | `{snippet}` |"
            )
        lines.append("")

    unrouted_hits = cands.get("matched_in_unrouted_contexts") or []
    lines.extend([
        "## 三、词典已收录但所在 `data-testid` 尚未被 DOM 路由放行的文案（前 60 条）",
        "",
        f"共发现 `{len(unrouted_hits)}` 条已可翻译文案挂载在未被 `antigravity_dom.js` 直接引用的 `data-testid` 上下文内：",
        "",
        "| 英文文案 | 状态 | 出现次数 | 未路由上下文示例 |",
        "| :--- | :--- | ---: | :--- |",
    ])
    for item in unrouted_hits[:60]:
        ctxs = ", ".join(f"`{c}`" for c in item["unrouted_contexts"][:4])
        lines.append(
            f"| `{_esc_md(item['text'])}` | `{item['status']}` | {item['count']} | {ctxs} |"
        )
    lines.append("")

    lines.extend([
        "## 四、按 UI 区域统计盲区与未路由容器",
        "",
        "| UI 区域 | Bundle `testid` 数 | 已路由 `testid` 数 | 已入词典未路由文案数 | 未命中英文候选数 | 未路由 `testid` 示例 |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
    ])
    for region, st in audit["regions"].items():
        samples = ", ".join(f"`{s}`" for s in st["sample_unrouted_testids"][:4]) or "—"
        lines.append(
            f"| {region} | {st['total_testids']} | {st['routed_testids']} | {st['matched_unrouted_candidates']} | {st['unmatched_candidates']} | {samples} |"
        )
    lines.append("")

    unmatched = cands.get("items") or []
    lines.extend([
        f"## 五、未命中词典的高频英文 UI 候选（Top {min(top, len(unmatched))} / 共 {len(unmatched)} 条）",
        "",
        "| # | 英文文案 | 次数 | 字段 | 上下文 `data-testid` |",
        "| ---: | :--- | ---: | :--- | :--- |",
    ])
    for idx, item in enumerate(unmatched[:top], 1):
        fields = ", ".join(f"`{f}`" for f in item["fields"])
        ctxs = ", ".join(f"`{c}`" for c in list((item.get("contexts") or {}).keys())[:3])
        lines.append(
            f"| {idx} | `{_esc_md(item['text'])}` | {item['count']} | {fields} | {ctxs} |"
        )
    lines.append("")

    if diff is not None:
        lines.extend([
            "## 六、版本间差异对比 (`--diff`)",
            "",
            f"- 新增 `data-testid`：`{len(diff['added_testids'])}` 个",
            f"- 移除 `data-testid`：`{len(diff['removed_testids'])}` 个",
            f"- 新增未命中英文候选：`{len(diff['added_unmatched'])}` 条",
            f"- 已解决英文候选：`{len(diff['resolved_unmatched'])}` 条",
            f"- 漂移原生锚点：`{len(diff['drifted_native_anchors'])}` 条",
            "",
        ])

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Antigravity 本地化离线审计与 UI 候选提取工具")
    parser.add_argument("--app-dir", default=None, help="Antigravity 安装目录")
    parser.add_argument("--language-server", default=None, help="显式指定 language_server 二进制路径")
    parser.add_argument("--bundle", default=None, help="直接指定前端 main.js 路径（跳过二进制提取）")
    parser.add_argument("--json", dest="json_out", default=None, help="输出完整 JSON 报告路径")
    parser.add_argument("--markdown", dest="md_out", default=None, help="输出 Markdown 审计报告路径")
    parser.add_argument("--diff", dest="diff_base", default=None, help="对比上一版 JSON 基线路径")
    parser.add_argument("--top", type=int, default=150, help="Markdown 报告中列出的未命中候选上限")
    args = parser.parse_args(argv)

    audit = run_audit(
        app_dir=args.app_dir,
        language_server_path=args.language_server,
        bundle_path=args.bundle,
    )
    diff_result = None
    if args.diff_base:
        old_data = json.loads(Path(args.diff_base).read_text(encoding="utf-8"))
        diff_result = diff_audits(old_data, audit)

    if args.json_out:
        out_p = Path(args.json_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_markdown_report(audit, top=args.top, diff=diff_result)
    if args.md_out:
        md_p = Path(args.md_out)
        md_p.parent.mkdir(parents=True, exist_ok=True)
        md_p.write_text(md, encoding="utf-8")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
