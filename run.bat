@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PYTHON_CMD=

where py >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    )
)

if not defined PYTHON_CMD (
    echo Python was not found on this computer.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

!PYTHON_CMD! main.py
if %errorlevel% neq 0 (
    pause
)

endlocal
