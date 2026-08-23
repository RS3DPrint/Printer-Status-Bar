# RS3D Printer Status Bar Custom PCB — Rev A

## Purpose
USB-only custom controller PCB for the RS3D Printer Status Bar. This replaces the Feather + separate level shifter + loose support parts with one compact board.

## Board target
- Approx. 78 mm x 22 mm, 2-layer
- USB-C receptacle on the short side so the housing can expose it from the side
- ESP32-S3-WROOM-1-N8 with onboard PCB antenna
- 5 V USB input powers the LED strip directly through a resettable fuse
- AP2112K generates 3.3 V for the ESP32-S3
- SN74AHCT1G125 converts GPIO5 data from 3.3 V to 5 V
- 330 ohm series resistor on LED data
- 1000 uF bulk capacitor on LED 5 V rail
- Native ESP32-S3 USB D-/D+ on GPIO19/GPIO20 for programming/debug
- RESET and BOOT buttons
- Optional STEMMA QT / Qwiic I2C connector
- 3-pin LED output: +5V, DATA, GND

## Firmware mapping
- WS2812 data: GPIO5
- USB D-: GPIO19
- USB D+: GPIO20
- I2C SDA: GPIO8
- I2C SCL: GPIO9
- Status LED: GPIO48
- BOOT: GPIO0
- RESET: EN

## Power
Use a quality 5 V USB-C supply. A 40-pixel WS2812B strip can approach ~2.4 A at full-brightness white. Firmware should enforce a reasonable global brightness limit. The board routes LED 5 V separately from the 3.3 V logic rail.

## IMPORTANT — Rev A status
This is an engineering prototype package. The electrical architecture is based on the manufacturers' reference data, but the supplied KiCad layout was generated without KiCad available in the build environment. Before ordering assembled production boards, open the project in KiCad, assign/verify the exact USB-C and ESP32 footprints, run ERC/DRC, verify antenna keepout, verify USB differential routing, and review the 5 V high-current path with your PCB assembler.

Do not treat Rev A as a safety-certified production board without hardware validation.
