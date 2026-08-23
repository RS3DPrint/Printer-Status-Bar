# Controller Profiles

## Athom: LS3P-WLED-LA
- Transport: WLED JSON API (`/json/state`, `/json/info`)
- Processor: ESP32-C3
- LED data: GPIO10
- Button: GPIO9
- Recommended firmware: factory WLED / ESP32-C3 WLED build
- Firmware updates: WLED web interface
- Battery reporting: unavailable

## Adafruit ESP32-S3 Feather
- Transport: RS3D device API (`/api/status`, `/api/info`)
- Processor: ESP32-S3
- LED data: GPIO5 / D5
- Firmware environment: `adafruit_feather_esp32s3`
- Optional battery reporting: onboard MAX17048

The application stores `controller_type` for every status bar and selects the appropriate transport automatically.

