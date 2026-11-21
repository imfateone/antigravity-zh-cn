# coding: utf-8
import glob
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _ag_common import (  # noqa: E402
    acquire_app_lock,
    find_app_dir,
    get_resources_dir,
    is_valid_asar,
    relaunch_antigravity,
    stop_antigravity_desktop_processes,
)


def _cleanup_temp_staging_dirs(resources_dir):
    for pattern in ("app.staging.*", "app.old.*"):
        for d in glob.glob(os.path.join(resources_dir, pattern)):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)


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
    try:
        with acquire_app_lock(resources_dir):
            print("[执行] 正在为您关闭 Antigravity 程序...")
            stop_antigravity_desktop_processes(app_dir, wait_timeout=8.0)

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
            has_valid_asar = os.path.exists(asar_path) and is_valid_asar(asar_path)
            if has_valid_asar:
                print("[状态] 检测到官方已存在有效的 app.asar，保留当前官方版本。")
                if os.path.exists(disabled_path):
                    try:
                        os.remove(disabled_path)
                        print("[清理] 已移除过期备份 app.asar.disabled")
                    except Exception as e:
                        print(f"[警告] 清理旧备份 app.asar.disabled 失败: {e}")
                if os.path.exists(unpacked_app_dir):
                    shutil.rmtree(unpacked_app_dir, ignore_errors=True)
                _cleanup_temp_staging_dirs(resources_dir)
                print("==================================================================")
                print("  还原成功！已保留官方原版客户端。")
                print("==================================================================")
                restored_or_clean = True
            elif os.path.exists(disabled_path):
                if not is_valid_asar(disabled_path):
                    print("[错误] app.asar.disabled 已损坏或格式无效，已中止还原以保护当前安装。")
                    return False

                print("[执行] 找到已禁用的原始语言包: app.asar.disabled")
                print("[执行] 正在恢复官方原版核心文件...")
                print("                                                                   ")

                if os.path.exists(asar_path):
                    try:
                        os.remove(asar_path)
                    except Exception as e:
                        print(f"[错误] 无法删除无效的 app.asar: {e}")
                        return False

                try:
                    os.rename(disabled_path, asar_path)
                    if os.path.exists(unpacked_app_dir):
                        shutil.rmtree(unpacked_app_dir, ignore_errors=True)
                    _cleanup_temp_staging_dirs(resources_dir)
                    print("==================================================================")
                    print("  还原成功！已恢复官方原版英文客户端。")
                    print("==================================================================")
                    restored_or_clean = True
                except Exception as e:
                    print(f"[错误] 恢复文件时出错: {e}")
                    return False
            else:
                if os.path.exists(asar_path):
                    print("[错误] 检测到 app.asar 已损坏且无 app.asar.disabled 可用，已中止清理以防应用无法启动。")
                    return False
                if os.path.exists(unpacked_app_dir):
                    print("[错误] 未找到 app.asar 或 app.asar.disabled，为避免损坏安装已中止清理 app 目录。")
                    return False
                print("[错误] 未找到 app.asar 或 app.asar.disabled。")
                return False
    except BlockingIOError as e:
        print(f"[提示] {e}")
        return False

    if restored_or_clean and relaunch:
        relaunch_antigravity(app_dir)
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
