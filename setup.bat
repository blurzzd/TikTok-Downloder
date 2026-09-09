@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PYTHON_CMD=

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py -3
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
        if !errorlevel! equ 0 (
            set PYTHON_CMD=python
        )
    )
)

if not defined PYTHON_CMD (
    echo Python 3.10 or newer was not found on this computer.
    echo.
    set /p INSTALL_CHOICE=Would you like to install Python now using winget? [Y/N]: 
    if /i "!INSTALL_CHOICE!"=="Y" (
        where winget >nul 2>nul
        if !errorlevel! equ 0 (
            echo.
            echo Installing Python with winget, this may take a few minutes...
            winget install --id Python.Python.3.12 -e --source winget
            if !errorlevel! neq 0 (
                echo.
                echo Automatic installation failed.
                echo Please install Python manually from https://www.python.org/downloads/
                echo Make sure to check "Add Python to PATH" during installation, then run setup.bat again.
                pause
                exit /b 1
            )
            echo.
            echo Python was installed. Please close this window and run setup.bat again
            echo so it can find the new Python installation.
            pause
            exit /b 0
        ) else (
            echo.
            echo winget is not available on this computer.
            echo Please install Python manually from https://www.python.org/downloads/
            echo Make sure to check "Add Python to PATH" during installation, then run setup.bat again.
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo Please install Python manually from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation, then run setup.bat again.
        pause
        exit /b 1
    )
)

echo Using Python: !PYTHON_CMD!
echo.
echo Installing required packages...
!PYTHON_CMD! -m pip install --user --upgrade pip >nul 2>nul
!PYTHON_CMD! -m pip install --user -r requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo Failed to install required Python packages.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo FFmpeg was not found on this computer.
    echo FFmpeg is required for audio-only downloads, video-only downloads, and
    echo combining separate audio/video streams.
    echo You can install it with "winget install Gyan.FFmpeg" or by downloading it
    echo from https://ffmpeg.org/download.html and adding it to your PATH.
    echo The application will still launch, but downloads may fail until FFmpeg is installed.
    echo.
)

if not exist "saved videos" mkdir "saved videos"

echo.
echo Setup finished successfully.
echo Launching TikTok Creator Downloader...
echo.
!PYTHON_CMD! main.py

endlocal
