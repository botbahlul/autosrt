#!/bin/sh

# ======================================================================
# PyPI build script
#
# Supported:
#   Linux (x86_64, aarch64, armv7l)
#   Android (Termux murni)
#   macOS
# ======================================================================

set -e

# ----------------------------------------------------------------------
# Find Python
# ----------------------------------------------------------------------
if [ -n "$PYTHON" ]; then
    PYTHON_CMD="$PYTHON"
elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_CMD="python3.10"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 was not found."
    exit 1
fi

# ----------------------------------------------------------------------
# Check Python version
# ----------------------------------------------------------------------
echo
echo "Using Python:"
"$PYTHON_CMD" --version

"$PYTHON_CMD" -c '
import sys
if sys.version_info < (3, 10):
    print("ERROR: Python 3.10 or newer is required.")
    sys.exit(1)
'

# ----------------------------------------------------------------------
# Detect operating system
# ----------------------------------------------------------------------
OS_NAME="$(uname -s)"
CPU_ARCH="$(uname -m)"

# Special detection for native Termux.
# /data/data/com.termux is also visible inside proot-distro,
# so its existence alone must NOT be used to identify Termux.
if [ "$OS_NAME" = "Linux" ]; then
    PYTHON_PREFIX="$("$PYTHON_CMD" -c 'import sys; print(sys.prefix)' 2>/dev/null)"

    case "$PYTHON_PREFIX" in
        /data/data/com.termux/files/usr*)
            OS_NAME="Android"
            ;;
    esac
fi

echo
echo "Operating system : $OS_NAME"
echo "Architecture     : $CPU_ARCH"

# ----------------------------------------------------------------------
# Clean previous build
# ----------------------------------------------------------------------
echo
echo "Cleaning previous build files..."
rm -rf build dist *.egg-info

# ----------------------------------------------------------------------
# Build tools
# ----------------------------------------------------------------------
echo
echo "Updating setuptools and wheel..."
"$PYTHON_CMD" -m pip install --upgrade setuptools wheel

# ----------------------------------------------------------------------
# Build source distribution (always contains ALL cross-platform binaries)
# ----------------------------------------------------------------------
echo
echo "Building source distribution..."
"$PYTHON_CMD" setup.py sdist

# ----------------------------------------------------------------------
# Build platform-specific wheel (contains only binaries for the active platform)
# ----------------------------------------------------------------------
case "$OS_NAME" in

    Darwin)
        echo
        echo "Detected macOS."
        if [ "$CPU_ARCH" = "x86_64" ]; then
            echo "Building macOS 10.15 x86_64 wheel..."
            "$PYTHON_CMD" setup.py bdist_wheel --plat-name macosx_10_15_x86_64
        else
            echo "Building automatic macOS wheel ($CPU_ARCH)..."
            "$PYTHON_CMD" setup.py bdist_wheel
        fi
        ;;

    Linux)
        echo
        echo "Detected Linux ($CPU_ARCH)."

        # Build native Linux wheel first.
        "$PYTHON_CMD" setup.py bdist_wheel

        echo "Checking auditwheel..."
        if ! command -v auditwheel >/dev/null 2>&1; then
            "$PYTHON_CMD" -m pip install --upgrade auditwheel
        fi

        case "$CPU_ARCH" in
            x86_64)
                MANYLINUX_PLAT="manylinux_2_17_x86_64"
                NATIVE_WHEEL="dist/*linux_x86_64.whl"
                ;;

            aarch64)
                MANYLINUX_PLAT="manylinux_2_17_aarch64"
                NATIVE_WHEEL="dist/*linux_aarch64.whl"
                ;;

            armv7l)
                MANYLINUX_PLAT="manylinux_2_17_armv7l"
                NATIVE_WHEEL="dist/*linux_armv7l.whl"
                ;;

            *)
                echo "ERROR: Unsupported Linux architecture: $CPU_ARCH"
                exit 1
                ;;
        esac

        echo
        echo "Running auditwheel repair..."
        echo "Target platform : $MANYLINUX_PLAT"
        echo "Input wheel     : $NATIVE_WHEEL"

        mkdir -p dist/repaired

        "$PYTHON_CMD" -m auditwheel repair \
            --plat "$MANYLINUX_PLAT" \
            --wheel-dir dist/repaired \
            $NATIVE_WHEEL

        echo "Replacing original Linux wheel..."
        rm -f $NATIVE_WHEEL
        mv dist/repaired/*.whl dist/
        rm -rf dist/repaired
        ;;
    Android)
        echo
        echo "Detected Termux Android ($CPU_ARCH)."
        echo "Building Android wheel..."
		# In a pure Termux environment, the standard bdist_wheel suffices, without auditwheel
		# (auditwheel/manylinux are irrelevant for the Bionic libc target).
        "$PYTHON_CMD" setup.py bdist_wheel
        ;;

    *)
        echo
        echo "ERROR: Unsupported operating system: $OS_NAME"
        exit 1
        ;;
esac

# ----------------------------------------------------------------------
# Check resulting distributions
# ----------------------------------------------------------------------
echo
echo "============================================================"
echo "Generated distributions"
echo "============================================================"
ls -lh dist/

# ----------------------------------------------------------------------
# Verify wheel metadata
# ----------------------------------------------------------------------
echo
echo "Checking distributions with twine..."
if command -v twine >/dev/null 2>&1; then
    twine check dist/*
else
    echo "WARNING: twine is not installed. Install it with: pip install twine"
fi

echo
echo "============================================================"
echo "BUILD SUCCESSFUL"
echo "============================================================"
