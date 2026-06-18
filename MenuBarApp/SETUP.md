# ModelRouter Menu Bar App

A native macOS status bar app (SwiftUI) that wraps the ModelRouter gateway.
Requires macOS 13 Ventura or later.

## Open in Xcode

```
open MenuBarApp/ModelRouterBar/ModelRouterBar.xcodeproj
```

Then press **⌘R** to build and run.

## First-time setup

1. Build and run once — the app appears in your menu bar as a branching-arrow icon with a status dot.
2. Click the icon → gear icon → enter your Gateway URL, Widget URL, and Master Key.
   - Gateway URL: `http://127.0.0.1:3000` (default)
   - Widget URL:  `http://localhost:8765` (default)
   - Master Key:  run `./mr key` in the repo root to get it
3. The app reads `~/Dev/modelrouter` as the default repo path for start/stop actions.
   If your repo is elsewhere, update `runMr()` in `GatewayState.swift`.

## What it shows

```
┌─────────────────────────────────────┐
│ ◉  ModelRouter         ↻  ⚙         │  ← status dot + controls
│ ────────────────────────────────── │
│ 🔒 Enterprise Mode          [ ON ] │  ← toggle
│    Locked to: anthropic            │
│    [ Allow Handoff ▾ ]             │  ← handoff button
│ ────────────────────────────────── │
│ 24h spend   $0.047 · 143 req       │
│ claude-sonnet  ████████  $0.041    │
│ gpt-4o-mini    ██        $0.004    │
│ groq-llama     █         $0.002    │
│ ────────────────────────────────── │
│ [Restart] [Stop]      [Widget][Log]│
└─────────────────────────────────────┘
```

## Enterprise mode

When **Enterprise Mode** is ON:
- The gateway locks routing to the designated family for each preset
  (defined in `config/model_families.yaml`).
- Fallbacks stay within that family (Opus → Sonnet → Haiku, never → GPT-4o).
- Cross-family routing is blocked.

**Allow Handoff** grants a one-shot override — the next routed request can
cross to another family. The lock is restored immediately after.

You can also control this from the CLI:

```bash
# Enable enterprise mode locked to Anthropic
python3 -m modelrouter.family_router on --family anthropic

# Grant a one-shot handoff to OpenAI (120s window)
python3 -m modelrouter.family_router handoff --family openai

# Check state
python3 -m modelrouter.family_router state

# Turn off
python3 -m modelrouter.family_router off
```

## Signing

The app runs unsigned locally (no App Store). For distribution:
1. Set your `DEVELOPMENT_TEAM` in Xcode → Target → Signing & Capabilities.
2. Archive and notarize with `xcrun notarytool`.

## Status dot colors

| Color  | Meaning                            |
|--------|------------------------------------|
| 🟢 Green  | Gateway healthy, all instances up  |
| 🟡 Yellow | Gateway responding but degraded    |
| 🔴 Red    | Gateway unreachable / down         |
| ⚫ Gray   | Status unknown / first check       |
