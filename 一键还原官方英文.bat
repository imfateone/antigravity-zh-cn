@echo off
chcp 65001 >nul
setlocal
set "RESTORE=%~dp0Restore.py"

where uv >nul 2>nul
if %errorlevel%==0 (
    uv run --no-sync python "%RESTORE%" --no-pause
    goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "%RESTORE%" --no-pause
    goto :done
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%RESTORE%" --no-pause
    goto :done
)

echo [ERROR] Python or uv not found in PATH.
pause
exit /b 1

:done
if errorlevel 1 (
    pause
    exit /b 1
)
timeout /t 2 >nul
