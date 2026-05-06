#!/usr/bin/env bash
set -euo pipefail

echo "=== Quickmark SSG - Build Script ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

check_dep() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: '$1' not found. Install it first."
        exit 1
    fi
}

case "${1:-help}" in
    install)
        echo "Installing build dependencies..."
        uv pip install pyinstaller httpx
        echo "Done."
        ;;

    build)
        check_dep pyinstaller
        echo "Building standalone executable..."
        pyinstaller quickmark.spec --clean --noconfirm
        echo "Build complete! Executable: dist/quickmark"
        ;;

    build-onefile)
        check_dep pyinstaller
        echo "Building single-file executable (larger but self-contained)..."
        pyinstaller gui.py \
            --onefile \
            --name quickmark \
            --noconsole \
            --add-data "template.html:." \
            --add-data "content:content" \
            --add-data "static:static" \
            --add-data "src:src" \
            --hidden-import httpx \
            --hidden-import flet \
            --clean \
            --noconfirm
        echo "Build complete! Executable: dist/quickmark"
        ;;

    clean)
        echo "Cleaning build artifacts..."
        rm -rf build/ dist/ *.spec __pycache__/ src/__pycache__/
        find . -name "*.spec" -not -name "quickmark.spec" -delete 2>/dev/null || true
        echo "Cleaned."
        ;;

    *)
        echo "Usage: $0 {install|build|build-onefile|clean}"
        echo ""
        echo "Commands:"
        echo "  install       Install PyInstaller and dependencies"
        echo "  build         Build using spec file (recommended)"
        echo "  build-onefile Build single-file executable"
        echo "  clean         Remove build artifacts"
        ;;
esac
