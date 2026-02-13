#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADDON_SRC="$SCRIPT_DIR/../addon/FreeCADMCP"
MOD_DIR="$HOME/snap/freecad/common/Mod"

rm -rf "$MOD_DIR/FreeCADMCP"
cp -r "$ADDON_SRC" "$MOD_DIR/FreeCADMCP"

echo "Deployed to $MOD_DIR/FreeCADMCP. Restart FreeCAD to pick up changes."
