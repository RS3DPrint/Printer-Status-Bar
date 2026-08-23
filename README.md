# RS3D Universal Printer Status Bar — MVP v0.1.1

A working prototype stack for a Wi-Fi addressable LED printer-status bar.

## What is included

- Windows-friendly controller with web dashboard on port **5055**
- Printer connector plug-in model
- **Klipper / Moonraker** status support
- **Bambu LAN MQTT** read-only status support
- Built-in simulator (no printer or ESP32 required)
- Multiple status bars mapped to multiple printers
- ESP32-S3 REST API for progress/color/state
- Remote test command
- Firmware binary upload endpoint for OTA-style updates
- PlatformIO firmware project for Adafruit ESP32-S3 Feather
- In-app hardware BOM for USB-C-only and rechargeable builds
- Versioned purchasing reference at `docs/PARTS_LIST.md` and machine-readable `data/bom.json`

## First test — no hardware needed

1. Double-click `run.bat`.
2. Open `http://localhost:5055`.
3. Click **Add Demo Setup**.
4. The demo printer will advance from 0–100% and the simulated bar receives its state.

## Klipper / Moonraker

Add a printer and select **Klipper / Moonraker**. Enter the Moonraker host, for example:

`192.168.1.50:7125`

The controller queries `print_stats`, `virtual_sdcard`, and `webhooks` through Moonraker.

## Bambu LAN

Add a printer and select **Bambu LAN**. Enter:

- Printer IP
- Printer serial number
- LAN access code

The connector uses local MQTT over TLS on port 8883 and subscribes to `device/{serial}/report`. Firmware/model settings can affect whether local read access is available.

## ESP32 firmware

1. Install VS Code + PlatformIO.
2. Copy `firmware/include/secrets.example.h` to `firmware/include/secrets.h`.
3. Fill in Wi-Fi SSID/password and device name.
4. Build/upload `firmware/` to the ESP32-S3 Feather.
5. Add the ESP32's IP as a Status Bar in the Windows dashboard.

Default firmware assumes **40 WS2812B LEDs** on GPIO 5. That is easy to change in `firmware/src/main.cpp`.

## API used by the bar

`POST /api/status`

```json
{
  "state": "printing",
  "progress": 63,
  "color": "#22c55e",
  "brightness": 96,
  "effect": "progress"
}
```

`GET /api/info` returns device/firmware/Wi-Fi information.

`POST /api/firmware` accepts a compiled firmware `.bin` as the raw request body.

## Hardware parts list

The controller dashboard includes a **Hardware BOM** section with separate USB-C-only and rechargeable build lists. The full purchasing/engineering reference is `docs/PARTS_LIST.md`. Its machine-readable source of truth is `data/bom.json`. Update the BOM version/date whenever hardware requirements change.

## Next build steps

- mDNS/SSDP auto-discovery of status bars
- printer auto-discovery
- configuration stored on the ESP32 instead of compile-time Wi-Fi secrets
- captive-portal first-time Wi-Fi setup
- real battery ADC calibration for the selected PCB/battery divider
- configurable color/effect rules in the Windows UI
- Windows service installer + tray application
- signed firmware and safer OTA update process
- enclosure/STL sized around final PCB, battery, magnets, diffuser and LED strip
