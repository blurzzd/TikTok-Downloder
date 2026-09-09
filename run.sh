#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

OS_NAME="$(uname -s)"

if [ "$OS_NAME" = "Linux" ] && [ -x "venv/bin/python" ]; then
    venv/bin/python main.py
elif command -v python3 >/dev/null 2>&1; then
    python3 main.py
else
    echo "Python was not found. Please run setup.sh first."
    exit 1
fi
