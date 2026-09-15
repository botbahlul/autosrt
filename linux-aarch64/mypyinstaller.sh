#!/bin/sh

# ----------------------------------------------------------------------
# Find Python
# ----------------------------------------------------------------------
if [ -n "$PYTHON" ]; then
    PYTHON_CMD="$PYTHON"
elif command -v python3.8 >/dev/null 2>&1; then
    PYTHON_CMD="python3.8"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 was not found."
    exit 1
fi

#echo "PYTHON_CMD = $PYTHON_CMD"


# ----------------------------------------------------------------------
# Check Python version
# ----------------------------------------------------------------------
echo
echo "Using Python:"
"$PYTHON_CMD" --version

"$PYTHON_CMD" -c '
import sys
if sys.version_info < (3, 8):
    print("ERROR: Python 3.8 or newer is required.")
    sys.exit(1)
' || exit 1


# ----------------------------------------------------------------------
# Detect operating system
# ----------------------------------------------------------------------
OS_NAME="$(uname -s)"
CPU_ARCH="$(uname -m)"

# Normalize Windows uname output (Git Bash / MSYS2 / Cygwin) to "Windows"
case "$OS_NAME" in
    MINGW*|MSYS*|CYGWIN*) OS_NAME="Windows" ;;
esac

# Special modification for running in a pure Termux environment
# Both `uname -s` and Python's `platform.system()` will still
# return "Linux" in Termux, so manual detection like this is mandatory
if [ "$OS_NAME" = "Linux" ] && [ -d "/data/data/com.termux" ]; then
    OS_NAME="Android"
fi

echo
echo "Operating system : $OS_NAME"
echo "Architecture     : $CPU_ARCH"


# ----------------------------------------------------------------------
# PyInstaller uses ':' as the src/dest separator on POSIX, ';' on Windows
# ----------------------------------------------------------------------
if [ "$OS_NAME" = "Windows" ]; then
    PYI_SEP=";"
else
    PYI_SEP=":"
fi

# ----------------------------------------------------------------------
# Clean previous build
# ----------------------------------------------------------------------
echo
echo "Cleaning previous build files..."

folder1="./build"
folder2="./dist"
file1="./autosrt.spec"

if [ -d "$folder1" ]; then
    rm -rf "$folder1"
fi

if [ -d "$folder2" ]; then
    rm -rf "$folder2"
fi

if [ -f "$file1" ]; then
    rm -f "$file1"
fi

set --

set -- "$@" \
	--hidden-import argparse \
	--onefile autosrt.py

echo
echo "Running: $PYTHON_CMD -m PyInstaller $*"
echo

"$PYTHON_CMD" -m PyInstaller "$@"
