# coding: utf-8
"""Shared standard-library helpers for Antigravity localization patcher & restore tools."""

from __future__ import annotations

import contextlib
import ctypes
import json
import os
import re
import struct
import subprocess
import sys
import time

CSIDL_DESKTOPDIRECTORY = 0x0010
_CREATION_FLAGS = 0x08000000 if sys.platform == "win32" else 0
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def extract_dir_from_exe_value(raw):
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
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
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
                                            cand = extract_dir_from_exe_value(v)
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
        ]
        for c in candidates:
            if c and os.path.isdir(os.path.join(c, "resources")):
                return c
        return ""
    if sys.platform == "darwin":
        return "/Applications/Antigravity.app" if os.path.isdir("/Applications/Antigravity.app") else ""
    return ""


def get_resources_dir(app_dir):
    if not app_dir:
        return ""
    if sys.platform == "darwin":
        return os.path.join(app_dir, "Contents", "Resources")
    return os.path.join(app_dir, "resources")


def _is_pid_alive(pid: int) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            err = ctypes.GetLastError()
            return err == 5  # ERROR_ACCESS_DENIED means process exists
        try:
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == 259  # STILL_ACTIVE
            return True
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


@contextlib.contextmanager
def acquire_app_lock(resources_dir: str, stale_seconds: float = 600.0):
    """Cross-process exclusive lock per Antigravity resources dir for Patcher/Restore."""
    os.makedirs(resources_dir, exist_ok=True)
    lock_path = os.path.join(resources_dir, ".ag-zh-patch.lock")
    fd = None
    for attempt in range(2):
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            payload = json.dumps({"pid": os.getpid(), "ts": time.time()}, separators=(",", ":"))
            os.write(fd, payload.encode("utf-8"))
            break
        except FileExistsError:
            stale = False
            if attempt == 0:
                try:
                    with open(lock_path, "r", encoding="utf-8") as lf:
                        info = json.load(lf)
                    lock_pid = info.get("pid") if isinstance(info, dict) else None
                    lock_ts = float(info.get("ts") or 0.0) if isinstance(info, dict) else 0.0
                    age = time.time() - lock_ts if lock_ts > 0 else stale_seconds + 1.0
                    if lock_pid is not None and not _is_pid_alive(int(lock_pid)):
                        stale = True
                    elif lock_pid is None and age > 5.0:
                        stale = True
                    elif age > stale_seconds and not (lock_pid and _is_pid_alive(int(lock_pid))):
                        stale = True
                except Exception:
                    try:
                        if time.time() - os.path.getmtime(lock_path) > 5.0:
                            stale = True
                    except OSError:
                        stale = True
            if stale and attempt == 0:
                try:
                    os.remove(lock_path)
                    continue
                except OSError:
                    pass
            raise BlockingIOError("已有另一个 Antigravity 汉化或还原任务正在运行，请等待其完成后重试。")
    try:
        yield lock_path
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.remove(lock_path)
        except OSError:
            pass


def get_desktop_dir():
    if sys.platform == "win32":
        try:
            buf = ctypes.create_unicode_buffer(260)
            hr = ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf)
            if hr == 0 and buf.value:
                return buf.value
        except Exception:
            pass
    base = os.environ.get("USERPROFILE", "") or os.path.expanduser("~")
    return os.path.join(base, "Desktop")


def _read_asar_header(asar_path):
    if not asar_path or not os.path.isfile(asar_path):
        return None
    file_size = os.path.getsize(asar_path)
    if file_size < 20:
        return None
    with open(asar_path, "rb") as f:
        data = f.read(16)
        if len(data) < 16:
            return None
        _magic, size, _u1, header_size = struct.unpack("<4I", data)
        if header_size <= 0 or size <= 0:
            return None
        if 16 + header_size > file_size or 8 + size > file_size:
            return None
        header_raw = f.read(header_size)
        if len(header_raw) != header_size:
            return None
        header = json.loads(header_raw.decode("utf-8"))
        if not isinstance(header, dict) or not isinstance(header.get("files"), dict):
            return None
        return file_size, 8 + size, header


def is_valid_asar(asar_path):
    try:
        return _read_asar_header(asar_path) is not None
    except Exception:
        return False


def _windows_path_patterns(app_dir=None):
    patterns = []
    if app_dir:
        patterns.append(os.path.abspath(app_dir).rstrip("\\/") + "\\*")
    else:
        local_default = os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "antigravity")
        if local_default:
            patterns.append(os.path.abspath(local_default).rstrip("\\/") + "\\*")
    return patterns


def list_antigravity_desktop_pids(app_dir=None):
    if sys.platform == "win32":
        patterns = _windows_path_patterns(app_dir)
        conds = " -or ".join(
            f"$_.ExecutablePath -like '{p.replace(chr(39), chr(39) * 2)}'" for p in patterns if p
        )
        if not conds:
            return []
        ps_cmd = (
            "Get-CimInstance Win32_Process | Where-Object { "
            f"$_.ExecutablePath -and ($_.ExecutablePath -notlike '*Antigravity IDE*') -and ({conds}) "
            "} | ForEach-Object { $_.ProcessId }"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                check=False,
                creationflags=_CREATION_FLAGS,
                timeout=10,
            )
            pids = []
            for line in (res.stdout or "").splitlines():
                line = line.strip()
                if line.isdigit():
                    pids.append(int(line))
            return pids
        except Exception:
            return []
    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["pgrep", "-f", "Antigravity"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return [int(x.strip()) for x in (res.stdout or "").splitlines() if x.strip().isdigit()]
        except Exception:
            return []
    return []


def is_antigravity_running(app_dir=None):
    if app_dir is not None or sys.platform != "win32":
        return bool(list_antigravity_desktop_pids(app_dir))
    return bool(list_antigravity_desktop_pids(find_app_dir() or None))


def _kill_windows_pids(app_dir=None):
    patterns = _windows_path_patterns(app_dir)
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
        capture_output=True,
        creationflags=_CREATION_FLAGS,
        timeout=15,
    )


def stop_antigravity_desktop_processes(app_dir=None, wait_timeout=8.0):
    """Stop only Antigravity 2.0 desktop processes (never Antigravity IDE) and wait for exit."""
    if sys.platform == "win32":
        pids = list_antigravity_desktop_pids(app_dir)
        if not pids:
            return
        _kill_windows_pids(app_dir)
        deadline = time.monotonic() + max(0.5, float(wait_timeout))
        second_kill_done = False
        start = time.monotonic()
        while time.monotonic() < deadline:
            remaining = list_antigravity_desktop_pids(app_dir)
            if not remaining:
                return
            if not second_kill_done and time.monotonic() - start >= 1.5:
                _kill_windows_pids(app_dir)
                second_kill_done = True
            time.sleep(0.3)
    elif sys.platform == "darwin":
        subprocess.run(["pkill", "-f", "Antigravity"], check=False, capture_output=True)
        deadline = time.monotonic() + max(0.5, float(wait_timeout))
        while time.monotonic() < deadline:
            if not list_antigravity_desktop_pids(app_dir):
                return
            time.sleep(0.3)


def split_windows_cmdline(cmdline: str) -> list[str]:
    """Split a Windows command-line argument string using CommandLineToArgvW quoting rules."""
    s = str(cmdline or "")
    n = len(s)
    i = 0
    args: list[str] = []
    while i < n:
        while i < n and s[i] in (" ", "\t", "\r", "\n"):
            i += 1
        if i >= n:
            break
        buf: list[str] = []
        in_quotes = False
        while i < n:
            ch = s[i]
            if not in_quotes and ch in (" ", "\t", "\r", "\n"):
                break
            if ch == "\\":
                bs_count = 0
                while i < n and s[i] == "\\":
                    bs_count += 1
                    i += 1
                if i < n and s[i] == '"':
                    buf.append("\\" * (bs_count // 2))
                    if bs_count % 2 == 1:
                        buf.append('"')
                        i += 1
                    else:
                        if in_quotes and i + 1 < n and s[i + 1] == '"':
                            buf.append('"')
                            i += 2
                        else:
                            in_quotes = not in_quotes
                            i += 1
                else:
                    buf.append("\\" * bs_count)
            elif ch == '"':
                if in_quotes and i + 1 < n and s[i + 1] == '"':
                    buf.append('"')
                    i += 2
                else:
                    in_quotes = not in_quotes
                    i += 1
            else:
                buf.append(ch)
                i += 1
        args.append("".join(buf))
    return args


def read_windows_shortcut(lnk_path: str) -> dict | None:
    """Read TargetPath, Arguments, WorkingDirectory, IconLocation, Description from a .lnk file."""
    if sys.platform != "win32" or not lnk_path or not os.path.isfile(lnk_path):
        return None
    lnk_ps = lnk_path.replace("'", "''")
    ps_cmd = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "$wsh = New-Object -ComObject WScript.Shell; "
        f"$s = $wsh.CreateShortcut('{lnk_ps}'); "
        "[PSCustomObject]@{"
        "TargetPath=[string]$s.TargetPath;"
        "Arguments=[string]$s.Arguments;"
        "WorkingDirectory=[string]$s.WorkingDirectory;"
        "IconLocation=[string]$s.IconLocation;"
        "Description=[string]$s.Description"
        "} | ConvertTo-Json -Compress"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=_CREATION_FLAGS,
            timeout=10,
        )
        raw = (res.stdout or "").strip()
        if res.returncode != 0 or not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def is_custom_wrapper_shortcut(target_path: str, arguments: str, exe_path: str) -> bool:
    """Return True when a shortcut targets an existing non-Antigravity launcher/wrapper."""
    target = str(target_path or "").strip()
    if not target:
        return False
    if os.path.basename(target).lower() == "antigravity.exe":
        return False
    return os.path.isfile(target)


def _ensure_debug_port_arg(args_list: list[str]) -> list[str]:
    out = list(args_list)
    if not any("--remote-debugging-port" in a.lower() for a in out):
        out.append("--remote-debugging-port=0")
    return out


def resolve_windows_launch_spec(
    app_dir: str,
    lnk_path: str | None = None,
    shortcut_reader=None,
) -> tuple[list[str], str]:
    """Resolve Windows relaunch command and working directory, honoring proxy/wrapper shortcuts."""
    exe_path = os.path.join(app_dir, "Antigravity.exe")
    default_cwd = os.path.dirname(exe_path)
    default_spec = ([exe_path, "--remote-debugging-port=0"], default_cwd)

    target_lnk = lnk_path if lnk_path is not None else os.path.join(get_desktop_dir(), "Antigravity.lnk")
    reader = shortcut_reader or read_windows_shortcut
    info = reader(target_lnk) if target_lnk else None
    if not isinstance(info, dict):
        return default_spec

    target = str(info.get("TargetPath") or "").strip()
    raw_args = str(info.get("Arguments") or "").strip()
    workdir = str(info.get("WorkingDirectory") or "").strip()

    if is_custom_wrapper_shortcut(target, raw_args, exe_path):
        parsed_args = split_windows_cmdline(raw_args)
        if "antigravity.exe" in raw_args.lower():
            parsed_args = _ensure_debug_port_arg(parsed_args)
        launch_cwd = workdir if (workdir and os.path.isdir(workdir)) else os.path.dirname(target)
        return ([target, *parsed_args], launch_cwd)

    if target and os.path.basename(target).lower() == "antigravity.exe":
        if os.path.normcase(os.path.abspath(target)) == os.path.normcase(os.path.abspath(exe_path)):
            parsed_args = split_windows_cmdline(raw_args)
            if parsed_args and parsed_args[0].lower().endswith(
                (".pyw", ".py", ".bat", ".cmd", ".vbs", ".ps1")
            ):
                return default_spec
            return ([exe_path, *_ensure_debug_port_arg(parsed_args)], default_cwd)

    return default_spec


def relaunch_antigravity(app_dir):
    if not app_dir:
        return False
    if sys.platform == "win32":
        cmd, launch_cwd = resolve_windows_launch_spec(app_dir)
        if cmd and os.path.exists(cmd[0]):
            clean_env = {
                k: v
                for k, v in os.environ.items()
                if k != "ELECTRON_RUN_AS_NODE"
                and not k.startswith(("ANTIGRAVITY_", "AGY_", "VSCODE_"))
            }
            subprocess.Popen(
                cmd,
                cwd=launch_cwd or os.path.dirname(cmd[0]),
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
            return True
    elif sys.platform == "darwin":
        subprocess.Popen(["open", app_dir])
        return True
    return False


def parse_semver(ver_str):
    s = str(ver_str or "").strip()
    if not s:
        return None
    m = re.match(r"^[vV]?(\d+)\.(\d+)\.(\d+)(?:\.\d+)?$", s)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def read_installed_ag_version(app_dir):
    if not app_dir:
        return ""
    res_dir = get_resources_dir(app_dir)
    pkg_path = os.path.join(res_dir, "app", "package.json")
    if os.path.isfile(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and str(data.get("version") or "").strip():
                return str(data["version"]).strip()
        except Exception:
            pass

    for candidate in (os.path.join(res_dir, "app.asar"), os.path.join(res_dir, "app.asar.disabled")):
        parsed = _read_asar_header(candidate)
        if not parsed:
            continue
        file_size, base_offset, header = parsed
        pkg_info = (header.get("files") or {}).get("package.json")
        if isinstance(pkg_info, dict) and "offset" in pkg_info and "size" in pkg_info:
            try:
                off = int(pkg_info["offset"])
                sz = int(pkg_info["size"])
                if off >= 0 and sz > 0 and base_offset + off + sz <= file_size:
                    with open(candidate, "rb") as af:
                        af.seek(base_offset + off)
                        pkg_data = json.loads(af.read(sz).decode("utf-8"))
                    if isinstance(pkg_data, dict) and str(pkg_data.get("version") or "").strip():
                        return str(pkg_data["version"]).strip()
            except Exception:
                pass

    if sys.platform == "win32":
        try:
            import winreg

            norm_app = os.path.normcase(os.path.abspath(app_dir))
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
                                child = winreg.EnumKey(root_k, idx)
                                with winreg.OpenKey(root_k, child) as ck:
                                    disp, _ = winreg.QueryValueEx(ck, "DisplayName")
                                    disp_s = str(disp or "").strip()
                                    if not disp_s.startswith("Antigravity") or "IDE" in disp_s:
                                        continue
                                    loc_dir = ""
                                    for val_name in ("InstallLocation", "DisplayIcon", "UninstallString"):
                                        try:
                                            v, _ = winreg.QueryValueEx(ck, val_name)
                                            loc_dir = extract_dir_from_exe_value(v)
                                            if loc_dir:
                                                break
                                        except OSError:
                                            continue
                                    if loc_dir and os.path.normcase(os.path.abspath(loc_dir)) == norm_app:
                                        ver, _ = winreg.QueryValueEx(ck, "DisplayVersion")
                                        return str(ver or "").strip()
                            except OSError:
                                continue
                except OSError:
                    continue
        except Exception:
            pass
    return ""


def _read_exe_file_version_windows(exe_path):
    if sys.platform != "win32" or not os.path.isfile(exe_path):
        return ""
    ps_literal = exe_path.replace("'", "''")
    ps_cmd = f"(Get-Item -LiteralPath '{ps_literal}').VersionInfo.FileVersion"
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            check=False,
            creationflags=_CREATION_FLAGS,
            timeout=10,
        )
        return (res.stdout or "").strip()
    except Exception:
        return ""


def cleanup_stale_updater_cache(app_dir, updater_dir=None, version_reader=None):
    """Remove cached Antigravity updater installers only when version <= installed version."""
    if sys.platform != "win32" and updater_dir is None:
        return []
    installed_ver = parse_semver(read_installed_ag_version(app_dir))
    if installed_ver is None:
        return []

    target_dir = updater_dir or os.path.join(os.getenv("LOCALAPPDATA", ""), "antigravity-updater")
    if not target_dir or not os.path.isdir(target_dir):
        return []

    read_ver = version_reader or _read_exe_file_version_windows
    removed = []

    top_installer = os.path.join(target_dir, "installer.exe")
    if os.path.isfile(top_installer):
        cached_ver = parse_semver(read_ver(top_installer))
        if cached_ver is not None and cached_ver <= installed_ver:
            try:
                os.remove(top_installer)
                removed.append(top_installer)
            except OSError:
                pass

    pending_dir = os.path.join(target_dir, "pending")
    if os.path.isdir(pending_dir):
        pending_exes = [
            os.path.join(pending_dir, fn)
            for fn in os.listdir(pending_dir)
            if fn.lower().endswith(".exe") and os.path.isfile(os.path.join(pending_dir, fn))
        ]
        for exe_file in pending_exes:
            cached_ver = parse_semver(read_ver(exe_file))
            if cached_ver is not None and cached_ver <= installed_ver:
                try:
                    os.remove(exe_file)
                    removed.append(exe_file)
                except OSError:
                    pass

        remaining_exes = [
            fn
            for fn in os.listdir(pending_dir)
            if fn.lower().endswith(".exe") and os.path.isfile(os.path.join(pending_dir, fn))
        ]
        if not remaining_exes:
            info_json = os.path.join(pending_dir, "update-info.json")
            if os.path.isfile(info_json):
                try:
                    os.remove(info_json)
                    removed.append(info_json)
                except OSError:
                    pass

    return removed
