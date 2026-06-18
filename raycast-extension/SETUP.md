# ModelRouter Raycast Extension

## Install

```bash
cd raycast-extension
npm install
npm run dev      # loads extension into Raycast for development
```

Raycast must be installed: https://raycast.com

## First-time preferences

After loading the extension in Raycast, open **Extensions → ModelRouter → Preferences**:

| Preference | Default | Notes |
|---|---|---|
| Gateway URL | `http://127.0.0.1:3000` | Change if running on a different port |
| Master Key | _(empty)_ | From `.env` → `MODELROUTER_MASTER_KEY`, or run `./mr key` |
| Widget Snapshot URL | `http://localhost:8765` | Used for cost data |
| ModelRouter Root Path | `~/Dev/modelrouter` | Needed for start/stop actions |

The extension reads `.env` automatically if you leave Master Key blank and set the correct Root Path.

## Commands

| Command | What it does |
|---|---|
| **Gateway Status** | Health indicator, instance count, start/stop/restart actions |
| **Switch Preset** | Browse all presets, copy model name / curl / Python snippet |
| **Cost Dashboard** | Spend by time window (1h/24h/7d/30d), per-model breakdown |
| **Copy Gateway Key** | Instant clipboard — no-view command, runs in background |

## Icon

Replace `icon.png` with a 512×512 PNG before publishing to the Raycast Store.
A simple dark background with a routing/split symbol works well.
You can convert the SVG at `icon.svg` with:

```bash
# requires Inkscape or rsvg-convert
rsvg-convert -w 512 -h 512 icon.svg > icon.png
# or with ImageMagick:
convert -background none icon.svg -resize 512x512 icon.png
```

## Publish to Raycast Store (optional)

```bash
npm run publish   # opens Raycast Store submission flow
```
