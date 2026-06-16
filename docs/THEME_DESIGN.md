# Receiver theme design thread

Visual language for the widget **CONNECTIVITY** bar — vintage hi-fi, lab gear, and industrial electronics.

## Design principles

1. **Discreet chrome** — theme lives in a header **Theme** menu; the receiver face stays clean.
2. **LEDs tell status** — color = state (ok / warn / down / skip); glow intensity = theme personality.
3. **Bezel matters** — round = pilot lamp; square = fuse/rack; dark recess = CRT/phosphor.
4. **Infinite override** — `tokens/config.json` → `receiver.led`, `receiver.background`, etc.

## Reference map (research notes)

| Theme | Inspiration | Visual cues |
|-------|-------------|-------------|
| Classic R/G | 1970s Marantz/Sansui | Red chassis, green power LED |
| Marantz | Marantz 2270 | Warm amber, bronze faceplate |
| McIntosh | MC252 / blue meters | Black glass, cyan meter glow |
| Denon | AVR silver era | Cool silver, ice-white LEDs |
| Pioneer | SX series | Charcoal, cyan accent |
| Tube Warm | Fender/Marshall tolex | Filament orange, slow glow pulse |
| Tek Scope | Tektronix 465 CRT | Green phosphor, dark bench |
| Luxman | L-509X | Gold lettering, dark wood tone |
| Nakamichi | ZX / Dragon era | Champagne silver, cool blue |
| Fuse Panel | Rack PDU / Hammond | Amber pilots, square bezels, gunmetal |
| Vintage Radio | Zenith/Philco dial | Cream dial, warm orange tuning glow |

## Future directions (your feedback welcome)

- [ ] VU-meter strip (decorative, tied to gateway load?)
- [ ] Backlit pushbutton texture for row labels
- [ ] Per-theme font (serif dial vs sans rack label)
- [ ] “Nixie” numeric preset indicator
- [ ] Subtle scanline overlay for CRT themes
- [ ] User-defined theme save to `config.local.json`

## Try a theme

Widget header → **Theme** → pick preset. Persists in browser (`localStorage`: `mr-receiver-preset`).

```json
// tokens/config.local.json — override one LED color
{
  "receiver": {
    "default_preset": "tube-warm",
    "led": { "ok": "#ffaa44" }
  }
}
```
