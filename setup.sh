#!/usr/bin/env bash
set -e

# Grab the directory you're running this from
DIR="$(pwd)"

# Target path for the launcher
TARGET="/usr/local/bin/pihole-mcp"

echo "Writing launcher to $TARGET (pointing at $DIR)..."

sudo tee "$TARGET" > /dev/null <<EOF
#!/bin/bash
cd $DIR
uv run mcp run main.py
EOF

sudo chmod +x "$TARGET"

echo "Done! You can now run 'pihole-mcp' from your AI client."
