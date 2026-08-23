# RS3D Universal Printer Status Bar — v0.3.5

Universal Windows controller + ESP32-S3 firmware for Wi-Fi 3D-printer status/progress light bars.

## Controller hardware support
- **Athom: LS3P-WLED-LA** uses stock WLED over its JSON API, ESP32-C3, and GPIO10 LED output.
- **Adafruit ESP32-S3 Feather** uses the RS3D device API and GPIO5/D5 LED output.
- Select the hardware profile when adding or editing each status bar. The desktop application chooses the correct network commands automatically.
- Update Athom firmware through WLED with an ESP32-C3 image. Never install Feather firmware on an Athom controller.

## Windows service
- Run `FULL_REINSTALL_KEEP_DATABASE.ps1` for a complete clean reinstall. It verifies a safety copy of `rs3d_status.db`, removes and rebuilds the service and Python environment, then reports the preserved printer/light-bar counts.
- Run `install_windows.ps1` to install the real `RS3DPrinterStatusBar` Windows service. Administrator approval is required.
- The installer uses standard 64-bit Python. If only a free-threaded Python build is present, it automatically installs compatible Python 3.12 through Windows Package Manager.
- The installer registers the pywin32 virtual-environment runtime before starting the service. Startup failures produce `C:\ProgramData\RS3D Printer Status Bar\service-startup-diagnostic.txt`.
- The service starts at boot, runs without a signed-in user, and is configured to restart after failures.
- Change **Server Port** under Settings, then run `restart_service.ps1` as administrator.
- Run `uninstall_service.ps1` to stop and remove the service.

## What is included
- Full fleet dashboard for printers and status bars
- Klipper / Moonraker and Bambu Lab LAN connectors
- Simulator for testing without hardware
- Per-bar assignment, brightness, effect, LED count, notes, and enable/disable
- Global state colors and live LED tests: progress, solid, pulse, chase, rainbow
- Device diagnostics: online state, firmware, Wi-Fi RSSI, battery hook, IP, uptime
- Local network discovery, OTA firmware upload, and remote reboot
- Separate rotating application, Windows-service, and light-bar communication logs
- Maintained USB-C and rechargeable BOM
- Browser/server mode plus dedicated Windows desktop-window mode

## Run on Windows
Run `run_desktop.bat` for desktop mode, or `run.bat` for browser/server mode at `http://localhost:5055`.

The launcher creates or repairs `.venv`, installs dependencies into that environment, and starts the controller.

## Printer setup
For Klipper/Moonraker, enter the Moonraker host such as `192.168.1.50:7125`.

For Bambu Lab LAN, enter printer IP, serial number, and LAN access code. The connector uses local MQTT over TLS on port 8883.

Network Scan listens for Bambu SSDP announcements on UDP 1990/2021, actively requests replies, and checks the local subnet for Bambu's secure MQTT service when multicast is unavailable.

## Log files
Logs are stored in `C:\ProgramData\RS3D Printer Status Bar\logs` and rotate automatically. Use `application.log` for program/discovery activity, `service.log` for Windows service startup and failures, and `lightbars.log` for Athom/Feather communication and state changes.

## Status bar firmware
Copy `firmware/include/secrets.example.h` to `firmware/include/secrets.h`, set Wi-Fi credentials/device name, and build/upload with PlatformIO. The current prototype firmware assumes 40 WS2812B LEDs on GPIO 5.

Device endpoints: `POST /api/status`, `GET /api/info`, `POST /api/reboot`, `POST /api/firmware`.

## Documentation
- `data/bom.json` — source-of-truth BOM
- `docs/PARTS_LIST.md` — USB-C and rechargeable hardware parts
- `docs/FEATURES.md` — application feature list
- `docs/ARCHITECTURE.md` — system architecture
