#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

OS_NAME="$(uname -s)"
PYTHON_BIN=""

find_python() {
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
            PYTHON_BIN="python3"
        fi
    fi
}

install_python_linux() {
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip python3-tk
        return $?
    fi
    if command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip python3-tkinter
        return $?
    fi
    if command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3 python3-pip python3-tkinter
        return $?
    fi
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip tk
        return $?
    fi
    if command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3 python3-pip python3-tk
        return $?
    fi
    return 1
}

install_python_macos() {
    if command -v brew >/dev/null 2>&1; then
        brew install python-tk
        return $?
    fi
    return 1
}

find_python

if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3.10 or newer was not found on this computer."
    echo ""
    read -r -p "Would you like to try installing it automatically now? [y/N]: " INSTALL_ANSWER
    if [ "$INSTALL_ANSWER" = "y" ] || [ "$INSTALL_ANSWER" = "Y" ]; then
        if [ "$OS_NAME" = "Linux" ]; then
            install_python_linux
            find_python
        elif [ "$OS_NAME" = "Darwin" ]; then
            install_python_macos
            find_python
        fi
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo ""
    echo "Automatic installation was not possible or was skipped."
    echo "Please install Python 3.10 or newer manually:"
    if [ "$OS_NAME" = "Darwin" ]; then
        echo "  https://www.python.org/downloads/macos/"
        echo "  or run: brew install python-tk"
    else
        echo "  https://www.python.org/downloads/"
        echo "  or use your distribution's package manager"
    fi
    echo "Then run this setup script again."
    exit 1
fi

echo "Using Python: $("$PYTHON_BIN" --version)"

if ! "$PYTHON_BIN" -c "import tkinter" >/dev/null 2>&1; then
    echo ""
    echo "The tkinter GUI module is not available for $PYTHON_BIN."
    if [ "$OS_NAME" = "Linux" ]; then
        echo "Try installing it with your package manager, for example:"
        echo "  sudo apt-get install python3-tk"
    else
        echo "Try installing it with: brew install python-tk"
    fi
    exit 1
fi

RUN_PYTHON=""

if [ "$OS_NAME" = "Linux" ]; then
    if [ ! -d "venv" ]; then
        if ! "$PYTHON_BIN" -m venv venv; then
            echo ""
            echo "Failed to create the virtual environment."
            exit 1
        fi
    fi
    venv/bin/pip install --upgrade pip >/dev/null
    if ! venv/bin/pip install -r requirements.txt; then
        echo ""
        echo "Failed to install required Python packages into the virtual environment."
        exit 1
    fi
    RUN_PYTHON="venv/bin/python"
else
    if ! "$PYTHON_BIN" -m pip install --user -r requirements.txt; then
        echo ""
        echo "Standard installation failed, retrying with --break-system-packages..."
        if ! "$PYTHON_BIN" -m pip install --user --break-system-packages -r requirements.txt; then
            echo ""
            echo "Failed to install required Python packages."
            exit 1
        fi
    fi
    RUN_PYTHON="$PYTHON_BIN"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo ""
    echo "FFmpeg was not found on this computer."
    echo "FFmpeg is required for audio-only downloads, video-only downloads, and"
    echo "combining separate audio/video streams."
    if [ "$OS_NAME" = "Darwin" ]; then
        echo "Install it with: brew install ffmpeg"
    else
        echo "Install it with your package manager, for example:"
        echo "  sudo apt-get install ffmpeg"
    fi
    echo "The application will still launch, but downloads may fail until FFmpeg is installed."
    echo ""
fi

mkdir -p "saved videos"
chmod +x run.sh
chmod +x setup.sh

echo ""
echo "Setup finished successfully."
echo "Launching TikTok Creator Downloader..."
echo ""
"$RUN_PYTHON" main.py
