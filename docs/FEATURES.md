# RS3D Printer Status Bar — Application Features

## v0.2.0
- Fleet dashboard with printer and status-bar health counts.
- Printer management for Klipper/Moonraker, Bambu LAN, and simulator connectors.
- Printer connection testing and enable/disable controls.
- Status-bar device management, printer assignment, notes, brightness, effect, and LED count.
- Live bar diagnostics: online/offline, firmware, Wi-Fi RSSI, battery hook, IP, uptime/device metadata.
- Lighting configuration for idle, preparing, printing, paused, complete, error, cancelled, offline, and unknown states.
- Live LED testing with progress, solid, pulse, chase, and rainbow effects.
- Network discovery scanner for RS3D bars on a local /24 subnet.
- OTA firmware upload and remote reboot controls.
- Maintained USB-C and rechargeable hardware BOM in both JSON and Markdown.
- Windows browser-hosted launcher plus desktop-window launcher (`run_desktop.bat`).

## Planned hardware-production work
- Rev A custom all-in-one PCB schematic and layout.
- Battery fuel-gauge calibration and production battery telemetry.
- Captive-portal first-time Wi-Fi provisioning.
- Signed firmware/update channel and automatic update checks.
- Production enclosure/STL/STEP files and magnetic mounting system.
