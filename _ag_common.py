# coding: utf-8
"""Shared standard-library helpers for Antigravity localization patcher & restore tools."""

from __future__ import annotations

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


def relaunch_antigravity(app_dir):
    if not app_dir:
        return False
    if sys.platform == "win32":
        exe_path = os.path.join(app_dir, "Antigravity.exe")
        if os.path.exists(exe_path):
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
