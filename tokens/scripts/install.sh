#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUPPORT="$HOME/Library/Application Support/TokenWidget"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST="$LAUNCH_AGENTS/com.kevinreed.tokenwidget.plist"
VENV="$ROOT/.venv"

echo "==> ModelRouter Keys install"
echo "    Root: $ROOT"

if ! command -v python3 >/dev/null; then
  echo "python3 is required" >&2
  exit 1
fi

echo "==> Creating venv + installing deps"
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r "$ROOT/requirements.txt"

echo "==> Fetching initial usage snapshot"
"$VENV/bin/python3" "$ROOT/scripts/fetch_usage.py" --print

mkdir -p "$SUPPORT" "$SUPPORT/sessions" "$LAUNCH_AGENTS"

REFRESH_INTERVAL="$(python3 -c "import json; from pathlib import Path; c=json.loads(Path('$ROOT/config.json').read_text()); print(int(c.get('refresh_interval_seconds',120)))")"

cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.kevinreed.tokenwidget</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV/bin/python3</string>
    <string>$ROOT/scripts/fetch_usage.py</string>
  </array>
  <key>StartInterval</key>
  <integer>${REFRESH_INTERVAL}</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$SUPPORT/fetch.log</string>
  <key>StandardErrorPath</key>
  <string>$SUPPORT/fetch.err.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/com.kevinreed.tokenwidget" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/com.kevinreed.tokenwidget"
launchctl kickstart -k "gui/$(id -u)/com.kevinreed.tokenwidget"

DESKTOP_APP="$HOME/Desktop/ModelRouter Keys.command"
cat >"$DESKTOP_APP" <<EOF
#!/usr/bin/env bash
exec "$ROOT/scripts/run_widget.sh"
EOF
chmod +x "$DESKTOP_APP"

AUTOSTART_PLIST="$LAUNCH_AGENTS/com.kevinreed.tokenwidget.panel.plist"
cat >"$AUTOSTART_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.kevinreed.tokenwidget.panel</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV/bin/python3</string>
    <string>$ROOT/widget/desktop_widget.py</string>
  </array>
  <key>RunAtLoad</key>
  <false/>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
EOF

echo ""
echo "Installed."
echo "  Snapshot:  $SUPPORT/snapshot.json"
echo "  Refresh:   every ${REFRESH_INTERVAL}s (launchd, runs even when widget is closed)"
echo "  Widget:    double-click '$DESKTOP_APP' or run:"
echo "             $VENV/bin/python3 $ROOT/widget/desktop_widget.py"
echo ""
echo "Auto-start panel at login (optional):"
echo "  launchctl bootstrap gui/\$(id -u) '$AUTOSTART_PLIST'"
echo ""
echo "Optional: install CodexBar for native WidgetKit widgets (requires macOS 14+):"
echo "  brew install --cask codexbar"
