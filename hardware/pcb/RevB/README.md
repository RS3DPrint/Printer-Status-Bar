# RS3D Printer Status Bar Custom PCB — Rev B

## What Rev B is
Rev B is the first **fabrication-candidate USB-only PCB package**. It integrates the ESP32-S3, USB-C power/programming path, USB ESD protection, 3.3 V regulator, 5 V LED supply path, 3.3-to-5 V WS2812 data buffer, LED series resistor, LED bulk capacitor, RESET/BOOT controls, status LED, Qwiic connector and 3-pin LED output.

Board target: **78 mm x 22 mm, 2-layer, 1.6 mm FR-4**. USB-C is on the short side to match the enclosure side opening. No battery and no physical power switch are included.

## Manufacturing files
The full fabrication package is in `RS3D_StatusBar_Custom_PCB_RevB.zip`. It contains Gerbers, plated drill data, BOM, CPL, assembly drawing, pin map, netlist, manufacturing notes, validation report, and Rev B PCB/schematic source.

## First order recommendation
Order **5 bare PCBs** or **2-5 assembled boards maximum** for Rev B bring-up. Inspect every Gerber in the PCB manufacturer's CAM viewer before payment. Verify USB-C footprint orientation and pin numbering against the exact GCT USB4105-GF-A-120 drawing.

## Required bring-up tests
1. Check 5 V to GND resistance before applying power.
2. Apply current-limited 5 V USB power with LEDs disconnected.
3. Confirm +3V3 regulator output.
4. Confirm ESP32-S3 enumerates over USB and can be flashed.
5. Verify Wi-Fi connection and OTA firmware.
6. Connect one WS2812 pixel first, then a short strip.
7. Validate data level at U3 and J2 with an oscilloscope if available.
8. Increase LED count/brightness while monitoring USB connector, fuse, traces and capacitor temperature.
9. Confirm Qwiic I2C bus and status LED.

## Engineering status
This package is **not safety-certified or mass-production-approved**. KiCad was unavailable in the generation environment, so ERC/DRC was not run with KiCad. The fabrication outputs were generated directly and checked for package completeness and design-rule intent, but they still require CAM review and prototype validation before production.
