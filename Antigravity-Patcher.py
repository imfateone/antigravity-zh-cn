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
    acquire_app_lock,
    cleanup_stale_updater_cache,
    find_app_dir,
    get_desktop_dir,
    get_resources_dir,
    is_antigravity_running,
    is_custom_wrapper_shortcut,
    read_windows_shortcut,
    relaunch_antigravity,
    split_windows_cmdline,
    stop_antigravity_desktop_processes,
)

from antigravity_localization import (  # noqa: E402
    DOM_TRANSLATOR_INJECTION,
    MENU_TRANSLATOR_INJECTION,
    SYSTEM_PROXY_INJECTION,
)

_resolve_resources_dir = get_resources_dir


APP_DIR = find_app_dir()
RESOURCES_DIR = _resolve_resources_dir(APP_DIR)
ASAR_PATH = os.path.join(RESOURCES_DIR, "app.asar") if RESOURCES_DIR else ""
UNPACKED_APP_DIR = os.path.join(RESOURCES_DIR, "app") if RESOURCES_DIR else ""


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

def replace_in_file(file_path, target, replacement, *, optional=False, expected_count=None):
    if not os.path.exists(file_path):
        return "missing_file"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    hits = content.count(target)
    if hits > 0:
        if expected_count is not None and hits != expected_count:
            label = os.path.basename(file_path)
            print(f"[警告] 替换命中次数异常（预期 {expected_count}，实际 {hits}），已跳过写入 ({label})")
            return "unexpected_count"
        updated = content.replace(target, replacement)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"[成功] 执行目标替换 ({os.path.basename(file_path)})")
        return "applied"
    if replacement in content:
        print(f"[跳过] 目标已替换 ({os.path.basename(file_path)})")
        return "already_applied"
    label = os.path.basename(file_path)
    snippet = target.replace("\n", "\\n")[:40]
    if optional:
        print(f"[跳过] 当前版本未包含该可选锚点 ({label}: {snippet})")
    else:
        print(f"[警告] 未找到替换锚点，已跳过写入 ({label}: {snippet})")
    return "not_found"

def ensure_desktop_shortcut(exe_path):
    if sys.platform != "win32" or not os.path.exists(exe_path):
        return
    desktop = get_desktop_dir()
    if not desktop or not os.path.exists(desktop):
        return
    lnk_path = os.path.join(desktop, "Antigravity.lnk")
    existing = read_windows_shortcut(lnk_path) if os.path.isfile(lnk_path) else None

    if existing and is_custom_wrapper_shortcut(
        existing.get("TargetPath"), existing.get("Arguments"), exe_path
    ):
        existing_args = str(existing.get("Arguments") or "").strip()
        existing_icon = str(existing.get("IconLocation") or "").strip()
        needs_port = (
            "antigravity.exe" in existing_args.lower()
            and "--remote-debugging-port" not in existing_args.lower()
        )
        needs_icon = (not existing_icon) or existing_icon.startswith(",")
        if not needs_port and not needs_icon:
            print(f"[保留] 检测到自定义代理/启动器快捷方式，已保留原配置: {lnk_path}")
            return
        lnk_ps = lnk_path.replace("'", "''")
        exe_ps = exe_path.replace("'", "''")
        ps_parts = [
            "$wsh = New-Object -ComObject WScript.Shell;",
            f"$s = $wsh.CreateShortcut('{lnk_ps}');",
        ]
        if needs_port:
            ps_parts.append("$s.Arguments = ($s.Arguments + ' --remote-debugging-port=0').Trim();")
        if needs_icon:
            ps_parts.append(f"$s.IconLocation = '{exe_ps},0';")
        ps_parts.append("$s.Save()")
        ps_cmd = " ".join(ps_parts)
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                check=True,
                creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            print(f"[保留] 已保留自定义启动器快捷方式并补齐配置: {lnk_path}")
        except Exception as e:
            print(f"[提示] 更新自定义快捷方式跳过: {e}")
        return

    if existing:
        existing_args = str(existing.get("Arguments") or "").strip()
        parsed_args = split_windows_cmdline(existing_args)
        if parsed_args and parsed_args[0].lower().endswith(
            (".pyw", ".py", ".bat", ".cmd", ".vbs", ".ps1")
        ) and "antigravity.exe" in existing_args.lower():
            print(
                f"[警告] 检测到桌面快捷方式疑似曾被旧版补丁覆盖，当前参数首项为脚本路径 ({parsed_args[0]})，"
                "请检查快捷方式 TargetPath 是否应恢复为对应启动器（如 pythonw.exe）。"
            )

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
    language_server_path = os.path.join(target_app_dir, "dist", "languageServer.js")
    tray_path = os.path.join(target_app_dir, "dist", "tray.js")
    updater_path = os.path.join(target_app_dir, "dist", "updater.js")

    append_once(preload_path, DOM_TRANSLATOR_INJECTION, "Antigravity Chinese Localization Engine", "Web UI Injection")
    replace_in_file(
        menu_path,
        "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);",
        "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel || item.__agOrigLabel === submenuLabel);",
        optional=True,
        expected_count=1,
    )
    append_once(menu_path, MENU_TRANSLATOR_INJECTION, "Antigravity Chinese Localization Engine - Menu", "Menu Translator Injection")
    append_once(
        language_server_path,
        SYSTEM_PROXY_INJECTION,
        "Antigravity Chinese Localization Engine - System Proxy Bridge",
        "System Proxy Bridge",
    )
    remove_injected_block(updater_path, "Antigravity Chinese Localization Engine - Auto Update Hook", "自动更新封锁 Hook")

    replace_in_file(
        tray_path,
        "(count > 0 ? `${count}` : 'No') +\n                    ' agent' +\n                    (count === 1 ? '' : 's') +\n                    ' running'",
        "(count > 0 ? `${count} 个智能体运行中` : '暂无运行中的智能体')",
        expected_count=1,
    )

    main_js_path = os.path.join(target_app_dir, "dist", "main.js")
    replace_in_file(main_js_path, "label: 'No agents running'", "label: '暂无运行中的智能体'", expected_count=1)
    replace_in_file(main_js_path, "label: `Open ${electron_1.app.getName()}`", "label: `打开 ${electron_1.app.getName()}`", expected_count=1)
    replace_in_file(main_js_path, "label: 'Quit'", "label: '退出'", expected_count=1)
    replace_in_file(main_js_path, "buttons: ['Cancel', 'Quit']", "buttons: ['取消', '退出']", expected_count=1)
    replace_in_file(main_js_path, "title: 'Confirm Quit'", "title: '确认退出'", expected_count=1)
    replace_in_file(main_js_path, "message: 'Are you sure you want to quit?'", "message: '确定要退出 Antigravity 吗？'", expected_count=1)
    replace_in_file(main_js_path, "detail: 'There may be agents or background tasks running.'", "detail: '当前可能仍有智能体或后台任务正在运行。'", expected_count=1)

    splash_path = os.path.join(target_app_dir, "dist", "provisionSplash.js")
    if os.path.exists(splash_path):
        with open(splash_path, "r", encoding="utf-8") as f:
            splash_content = f.read()
        patched_splash = splash_content.replace("Setting up WSL: ", "正在配置 WSL: ")
        if patched_splash != splash_content:
            with open(splash_path, "w", encoding="utf-8") as f:
                f.write(patched_splash)
            print(f"[成功] 已成功汉化 WSL 启动界面 ({os.path.basename(splash_path)})")


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

    try:
        with acquire_app_lock(RESOURCES_DIR):
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
    except BlockingIOError as e:
        print(f"[提示] {e}")
        return False

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
