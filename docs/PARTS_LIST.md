# RS3D Universal Printer Status Bar — Parts List / BOM

**BOM version:** 0.1.0  
**Updated:** 2026-08-22  
**Hardware revision:** Prototype A  
**Target enclosure:** approximately 250 mm magnetic Wi-Fi status bar

This document is the purchasing reference for the current prototype. The same BOM is displayed inside the Windows controller dashboard and should be updated whenever the hardware design changes.

## Variant A — USB-C powered / no battery

Buy the following for one prototype:

| Qty | Part | Minimum / target specification |
|---:|---|---|
| 1 | Adafruit ESP32-S3 Feather | ESP32-S3, 4MB Flash, 2MB PSRAM, onboard PCB antenna, USB-C |
| 1 | Addressable LED strip | WS2812B-compatible, 5V, 5 mm wide preferred, 120-160 LEDs/m, about 250 mm |
| 1 | 74AHCT125 | 3.3V-to-5V logic-level translation for LED data |
| 1 | 330-470 ohm resistor | LED data-line resistor |
| 1 | 1000 uF capacitor | At least 6.3V, across LED 5V/GND near strip input |
| 1 | USB-C power adapter | 5V/2A minimum; 5V/3A preferred for development |
| 1 | USB-C cable | Power + programming capable |
| 1 | Slide switch | Small enclosure-mount switch |
| 1 set | 22-26 AWG stranded wire | Heavier wire on power paths |
| 1 set | Heat-shrink / connectors | JST/locking connectors as needed |
| 1 | PETG enclosure | Initial target ~250 x 20 x 18 mm |
| 1 | Frosted diffuser | 5-8 mm visible width, about 250 mm long |
| 6 | Neodymium magnets | Target 8-10 mm diameter x 2-3 mm thick |
| 2 | M3 screws | Optional non-magnetic mounting |

### USB-only power path

`5V USB-C -> controller / 5V rail -> LED strip`

The ESP32 produces the LED commands. The 74AHCT125 converts the ESP32's 3.3V data signal to a robust 5V data signal for the LEDs.

## Variant B — Rechargeable battery / USB-C

Use **all common parts above**, plus the following battery-specific parts. The ESP32-S3 Feather's onboard LiPo support is useful for development, but the high-current LED rail must be designed separately.

| Qty | Part | Minimum / target specification |
|---:|---|---|
| 1 | Protected 1S LiPo battery | 3.7V nominal, **5000 mAh target**, correct JST polarity, dimensions matched to final enclosure |
| 1 | 5V boost or buck-boost regulator | Stable 5V, target >=2A continuous until final LED current is measured |
| 1 | Battery power wiring/connectors | Sized for the selected current |

### Battery power path

`3.7V LiPo -> 5V regulator -> LED strip / 5V system rail`

`USB-C -> controller/charger -> LiPo`

The final production design may use a dedicated charger/power-path IC rather than relying on prototype-board power routing.

## What NOT to buy yet

Do not order large production quantities of batteries, regulators, custom PCBs, diffusers, magnets, or enclosure hardware yet. Prototype A is intended to determine actual LED brightness/current, heat, runtime, magnet strength, Wi-Fi performance and physical fit first.

## Production PCB direction

Once Prototype A is validated, the separate ESP32 Feather, regulator module, level shifter and much of the wiring should become one custom RS3D PCB containing:

- ESP32-S3 module with onboard antenna
- USB-C connector and protection
- 1S LiPo charging/power-path circuit
- battery voltage measurement
- 5V LED power regulation
- 3.3V-to-5V LED data buffer
- power/load control
- switch input
- LED connector
- programming/recovery pads
- temperature/current protection as required by final design

## Safety / validation gates before selling

1. Verify peak and normal LED current at the firmware's maximum allowed brightness.
2. Verify regulator and wiring temperatures during long prints.
3. Use a protected LiPo from a qualified supplier and verify polarity.
4. Verify charging behavior while LEDs are active.
5. Verify enclosure temperature around the battery and regulator.
6. Add proper battery retention so magnets or drops cannot damage the cell.
7. Complete applicable battery shipping, product-safety and regulatory review before retail sale.

The machine-readable source of truth is `data/bom.json`.
