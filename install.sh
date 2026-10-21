#!/usr/bin/env bash
# Install the claude-motion-film skill into a DeepSeek Harness / Claude-style skill dir.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/claude-motion-film"
DEST="${1:-$HOME/.dsh/skills}"
mkdir -p "$DEST"
rm -rf "$DEST/claude-motion-film"
cp -r "$SRC" "$DEST/claude-motion-film"
echo "installed -> $DEST/claude-motion-film"
echo "start a new session, then ask your agent to use the skill."
