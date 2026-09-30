#!/usr/bin/env bash
# Minecraft 2D — static web preview server.
# Serves the prebuilt static directory ./dist in the FOREGROUND on $PORT (default 3000)
# and records the deployment output for the controller.
set -euo pipefail
time -p cd "$(dirname "$0")"
time -p test -f dist/index.html
time -p mkdir -p /home/runner/work/_temp/omgithub-web
time -p python3 -c "import json; json.dump({'project': '/home/runner/work/PlayGround/PlayGround', 'directory': '/home/runner/work/PlayGround/PlayGround/dist'}, open('/home/runner/work/_temp/omgithub-web/deployment-output.json', 'w'))"
time -p cat /home/runner/work/_temp/omgithub-web/deployment-output.json
PORT="${PORT:-3000}"
time -p echo "Serving Minecraft 2D web build from ./dist on port $PORT"
exec python3 -m http.server "$PORT" --bind 0.0.0.0 --directory dist
