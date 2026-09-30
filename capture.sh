#!/usr/bin/env bash
# Capture desktop + mobile screenshots of the exact $CAPTURE_URL into $CAPTURE_DIR.
# Leaves the app running; only closes its own browser.
# Exit 75 = temporary navigation/browser infra failure, exit 1 = script/rendering defect.
set -euo pipefail
time -p test -n "${CAPTURE_URL:-}" || { echo 'CAPTURE_URL is required' >&2; exit 1; }
time -p test -n "${CAPTURE_DIR:-}" || { echo 'CAPTURE_DIR is required' >&2; exit 1; }
time -p test -n "${RUNTIME_DIR:-}" || { echo 'RUNTIME_DIR is required' >&2; exit 1; }
case "$CAPTURE_DIR" in
  /home/runner/work/PlayGround/PlayGround/*)
    echo "CAPTURE_DIR must stay outside the source tree: $CAPTURE_DIR" >&2
    exit 1
    ;;
esac
time -p mkdir -p "$CAPTURE_DIR"
time -p node "${RUNTIME_DIR}/scripts/default-capture.mjs"
status=$?
time -p test -f "$CAPTURE_DIR/final-desktop.png" || { echo 'missing final-desktop.png' >&2; exit 1; }
time -p test -f "$CAPTURE_DIR/final-mobile.png" || { echo 'missing final-mobile.png' >&2; exit 1; }
time -p ls -la "$CAPTURE_DIR"
exit "$status"
