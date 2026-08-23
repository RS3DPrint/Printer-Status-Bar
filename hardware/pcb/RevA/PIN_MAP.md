# RS3D Custom PCB Rev A Pin Map

| Function | ESP32-S3 module pin | GPIO |
|---|---:|---:|
| LED DATA to AHCT buffer | 5 | GPIO5 |
| I2C SDA / Qwiic | 12 | GPIO8 |
| I2C SCL / Qwiic | 17 | GPIO9 |
| USB D- | 13 | GPIO19 |
| USB D+ | 14 | GPIO20 |
| BOOT | 27 | GPIO0 |
| Status LED | 25 | GPIO48 |
| UART RX | 36 | GPIO44 |
| UART TX | 37 | GPIO43 |
| Reset | 3 | EN |
| 3.3 V power | 2 | 3V3 |
| Ground | 1, 40, EPAD 41 | GND |

## LED connector J2
1. +5V_LED
2. LED_DATA_5V
3. GND

## Qwiic connector J3
1. GND
2. +3V3
3. SDA / GPIO8
4. SCL / GPIO9
