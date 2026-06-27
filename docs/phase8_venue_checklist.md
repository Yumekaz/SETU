# Phase 8 Venue Checklist

Use before live presentation or venue dress rehearsal.

## Hardware

- [ ] Laptop charged + power adapter
- [ ] HDMI/USB-C adapter tested with venue projector
- [ ] Resolution 1280×720 minimum (1920×1080 preferred)
- [ ] Browser: Chrome or Firefox, zoom 100%

## Software (day before)

- [ ] `docker compose build` completed OR local venv + `npm install` done
- [ ] `bash scripts/demo_preflight.sh` → `PREFLIGHT=PASS`
- [ ] `python3 scripts/cache_demo_tiles.py` (offline map tiles)
- [ ] Copy repo to USB backup (optional)

## Network

- [ ] Demo works with **Wi-Fi off** (cache mode)
- [ ] If venue Wi-Fi required, test `localhost` only — no external deps in demo path

## Cold-start rehearsal

```bash
SETU_BROWSER_COLD_START=1 python3 scripts/phase6_browser_gate.py
```

Allow up to 3 min for first bootstrap.

## Short-script card

Print or phone-note: if MC says "1 minute left", switch to **Short** script in [phase8_demo_script.md](phase8_demo_script.md) — skip trend chart, fast backtest scrub to headline, one unrehearsed click.