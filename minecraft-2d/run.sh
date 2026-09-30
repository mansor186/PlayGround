#!/usr/bin/env bash
# تشغيل ماين كرافت 2D
set -euo pipefail
cd "$(dirname "$0")"
if ! python3 -c "import pygame" 2>/dev/null; then
  echo "Installing pygame..."
  pip3 install -r requirements.txt
fi
exec python3 main.py
