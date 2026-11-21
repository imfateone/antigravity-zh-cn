# coding: utf-8
import os
import re
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _extract_dir_from_exe_value(raw):
    val = str(raw or "").strip()
    if not val:
        return ""
    if val.startswith('"'):
        end_q = val.find('"', 1)
        if end_q > 1:
            val = val[1:end_q]
    else:
        val = val.split(",")[0].strip()
        m = re.match(r"^(.*?\.exe)\b", val, re.IGNORECASE)
        if m:
            val = m.group(1)
    p = os.path.dirname(val) if val.lower().endswith(".exe") else val
    return p if p and os.path.isdir(os.path.join(p, "resources")) else ""


def find_app_dir():
    if sys.platform == "win32":
        env_dir = (os.environ.get("ANTIGRAVITY_APP_DIR") or "").strip().strip('"')
        if env_dir and os.path.isdir(os.path.join(env_dir, "resources")):
            return env_dir

        try:
            import winreg

            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\121a0be4-63bd-531e-acf8-fc3924c7e984",
                ) as k:
                    loc, _ = winreg.QueryValueEx(k, "InstallLocation")
                    loc = str(loc or "").strip().strip('"')
                    if loc and os.path.isdir(os.path.join(loc, "resources")):
                        return loc
            except OSError:
                pass

            uninstall_roots = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, subkey in uninstall_roots:
                try:
                    with winreg.OpenKey(hive, subkey) as root_k:
                        count = winreg.QueryInfoKey(root_k)[0]
                        for idx in range(count):
                            try:
                                child_name = winreg.EnumKey(root_k, idx)
                                with winreg.OpenKey(root_k, child_name) as ck:
                                    disp, _ = winreg.QueryValueEx(ck, "DisplayName")
                                    disp_s = str(disp or "").strip()
                                    if not disp_s.startswith("Antigravity") or "IDE" in disp_s:
                                        continue
                                    for val_name in ("InstallLocation", "DisplayIcon", "UninstallString"):
                                        try:
                                            v, _ = winreg.QueryValueEx(ck, val_name)
                                            cand = _extract_dir_from_exe_value(v)
                                            if cand:
                                                return cand
                                        except OSError:
                                            continue
                            except OSError:
                                continue
                except OSError:
                    continue
        except Exception:
            pass

        candidates = [
            os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "antigravity"),
            os.path.join(os.getenv("ProgramFiles", ""), "Antigravity"),
            r"D:\Tools\Antigravity\antigravity",
            r"D:\Tools\Antigravity",
        ]
        for c in candidates:
            if c and os.path.isdir(os.path.join(c, "resources")):
                return c
        return ""
    if sys.platform == "darwin":
        return "/Applications/Antigravity.app" if os.path.isdir("/Applications/Antigravity.app") else ""
    return ""


def get_resources_dir(app_dir):
    if sys.platform == "darwin":
        return os.path.join(app_dir, "Contents", "Resources")
    return os.path.join(app_dir, "resources")


def stop_antigravity_desktop_processes(app_dir):
    """Stop only Antigravity 2.0 desktop processes (never Antigravity IDE)."""
    if sys.platform == "win32":
        patterns = []
        if app_dir:
            patterns.append(os.path.abspath(app_dir).rstrip("\\/") + "\\*")
        local_default = os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "antigravity")
        if local_default:
            pat = os.path.abspath(local_default).rstrip("\\/") + "\\*"
            if pat not in patterns:
                patterns.append(pat)
        conds = " -or ".join(
            f"$_.ExecutablePath -like '{p.replace(chr(39), chr(39) * 2)}'" for p in patterns if p
        )
        if not conds:
            return
        ps_cmd = (
            "Get-CimInstance Win32_Process | Where-Object { "
            f"$_.ExecutablePath -and ($_.ExecutablePath -notlike '*Antigravity IDE*') -and ({conds}) "
            "} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            check=False,
            creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    elif sys.platform == "darwin":
        os.system("pkill -f Antigravity >/dev/null 2>&1")


def restore(relaunch=True):
    app_dir = find_app_dir()
    if not app_dir:
        print("[错误] 未检测到 Antigravity 桌面端安装目录。")
        return False

    resources_dir = get_resources_dir(app_dir)
    if not os.path.isdir(resources_dir):
        print(f"[错误] 未找到 Antigravity 资源目录: {resources_dir}")
        return False

    asar_path = os.path.join(resources_dir, "app.asar")
    disabled_path = asar_path + ".disabled"
    unpacked_app_dir = os.path.join(resources_dir, "app")

    print("==================================================================")
    print("                                                                ")
    print("             Antigravity 桌面端 纯净版还原工具                    ")
    print("基于开源项目: https://github.com/MIMICTE/Antigravity-zh-CN (MIT)")
    print("                                                                ")
    print("==================================================================")
    print("                                                                   ")
    print(f"[目录] Antigravity 路径: {app_dir}")
    print("[执行] 正在为您关闭 Antigravity 程序...")
    stop_antigravity_desktop_processes(app_dir)

    update_yml = os.path.join(resources_dir, "app-update.yml")
    disabled_update_yml = update_yml + ".disabled"
    if os.path.exists(disabled_update_yml):
        try:
            if not os.path.exists(update_yml):
                os.rename(disabled_update_yml, update_yml)
                print("[恢复] 已恢复官方自动更新配置: app-update.yml")
            else:
                os.remove(disabled_update_yml)
        except Exception as e:
            print(f"[警告] 恢复 app-update.yml 失败: {e}")

    restored_or_clean = False
    if os.path.exists(disabled_path):
        print("[执行] 找到已禁用的原始语言包: app.asar.disabled")
        print("[执行] 正在恢复官方原版核心文件...")
        print("                                                                   ")

        if os.path.exists(asar_path):
            try:
                os.remove(asar_path)
            except Exception as e:
                print(f"[错误] 无法删除当前的 app.asar: {e}")
                return False

        try:
            os.rename(disabled_path, asar_path)
            if os.path.exists(unpacked_app_dir):
                shutil.rmtree(unpacked_app_dir, ignore_errors=True)
            print("==================================================================")
            print("  还原成功！已恢复官方原版英文客户端。")
            print("==================================================================")
            restored_or_clean = True
        except Exception as e:
            print(f"[错误] 恢复文件时出错: {e}")
            return False
    else:
        if os.path.exists(unpacked_app_dir):
            print("[状态] 未发现 app.asar.disabled，正在清理汉化注入残留目录...")
            shutil.rmtree(unpacked_app_dir, ignore_errors=True)
            print("==================================================================")
            print("  清理成功！软件当前已是原版状态。")
            print("==================================================================")
            restored_or_clean = True
        else:
            print("[状态] 未发现已禁用的语言包 (app.asar.disabled)。")
            print("[状态] 软件当前已经是原版纯净状态。")
            print("==================================================================")
            restored_or_clean = True

    if restored_or_clean and relaunch:
        if sys.platform == "win32":
            exe_path = os.path.join(app_dir, "Antigravity.exe")
            if os.path.exists(exe_path):
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                clean_env = {
                    k: v
                    for k, v in os.environ.items()
                    if k != "ELECTRON_RUN_AS_NODE"
                    and not k.startswith(("ANTIGRAVITY_", "AGY_", "VSCODE_"))
                }
                subprocess.Popen(
                    [exe_path, "--remote-debugging-port=0"],
                    cwd=os.path.dirname(exe_path),
                    env=clean_env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True,
                )
        elif sys.platform == "darwin":
            subprocess.Popen(["open", app_dir])
    return restored_or_clean


if __name__ == "__main__":
    no_pause = "--no-pause" in sys.argv
    relaunch = "--no-relaunch" not in sys.argv
    exit_code = 0
    try:
        if not restore(relaunch=relaunch):
            exit_code = 1
        if not no_pause:
            input("\n执行完毕，按 Enter 键退出...")
    except KeyboardInterrupt:
        print("\n\n[提示] 用户取消操作。")
        if not no_pause:
            input("\n按 Enter 键退出...")
    except Exception as e:
        print(f"\n[错误] 执行过程中出现异常: {e}")
        print("\n如果问题持续，请访问 GitHub 提交 Issue:")
        print("https://github.com/MIMICTE/Antigravity-zh-CN/issues")
        if not no_pause:
            input("\n按 Enter 键退出...")
        exit_code = 1
    sys.exit(exit_code)
