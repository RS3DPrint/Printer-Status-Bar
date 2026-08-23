# RS3D Universal Printer Status Bar — v0.2.0

Universal Windows controller + ESP32-S3 firmware for Wi-Fi 3D-printer status/progress light bars.

## What is included

- Full fleet dashboard for printers and status bars
- Klipper / Moonraker printer connector
- Bambu Lab LAN MQTT connector
- Simulator for testing without hardware
- Per-bar printer assignment, brightness, effect, LED count, notes, and enable/disable
- Global status colors for idle, preparing, printing, paused, complete, error, cancelled, offline, and unknown
- Live LED testing: progress, solid, pulse, chase, rainbow
- Device diagnostics: online state, firmware, Wi-Fi RSSI, battery hook, IP, uptime
- Local network discovery for RS3D bars
- OTA firmware upload and remote reboot
- Maintained USB-C and rechargeable BOM
- ESP32-S3 PlatformIO firmware project
- Browser/server mode and dedicated Windows desktop-window mode

## Run on Windows

### Desktop app mode
Run:

`run_desktop.bat`

This creates/repairs `.venv`, installs dependencies, starts the local controller, and opens the dashboard in a dedicated Windows desktop window.

### Browser/server mode
Run:

`run.bat`

Then open `http://localhost:5055`.

## Printer setup

### Klipper / Moonraker
Choose **Creality / Klipper / Moonraker** and enter the Moonraker host, normally something like:

`192.168.1.50:7125`

The connector reads print state/progress through Moonraker.

### Bambu Lab LAN
Choose **Bambu Lab LAN** and enter the printer IP, serial number, and LAN access code. The connector uses local MQTT over TLS on port 8883 and subscribes to `device/{serial}/report`.

## Status bar firmware

1. Install VS Code + PlatformIO.
2. Copy `firmware/include/secrets.example.h` to `firmware/include/secrets.h`.
3. Set Wi-Fi SSID/password and device name.
4. Build/upload the `firmware/` project to the ESP32-S3.
5. Add the bar by IP in the app, or use network discovery.

The current prototype firmware assumes 40 WS2812B LEDs on GPIO 5.

## Device API

- `POST /api/status` — set state, progress, color, brightness, and effect
- `GET /api/info` — firmware/device/Wi-Fi/battery-hook information
- `POST /api/reboot` — restart the controller
- `POST /api/firmware` — upload a compiled firmware `.bin`

## Hardware documentation

- `data/bom.json` — machine-readable source-of-truth BOM
- `docs/PARTS_LIST.md` — USB-C and rechargeable prototype/production parts notes
- `docs/FEATURES.md` — current application feature list and upcoming hardware work
- `docs/ARCHITECTURE.md` — system architecture

## Next production hardware work

- Rev A all-in-one custom PCB
- Battery fuel-gauge calibration
- Captive-portal first-time Wi-Fi provisioning
- Signed firmware/update channel
- Magnetic PETG enclosure and diffuser CAD/STL/STEP files
