EESchema Schematic File Version 4
LIBS:power
LIBS:device
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "RS3D Printer Status Bar USB Rev A"
Comment1 "ESP32-S3-WROOM-1-N8 / USB-C / WS2812B"
Comment2 "Engineering prototype"
$EndDescr
Text Notes 900 900 0 120 ~ 24
USB-C J1 -> F1 -> +5V_SYS -> LED J2 + U2 AP2112
Text Notes 900 1300 0 100 ~ 20
J1 D- -> U4 USBLC6-2SC6 -> R3 22R -> U1 GPIO19
Text Notes 900 1600 0 100 ~ 20
J1 D+ -> U4 USBLC6-2SC6 -> R4 22R -> U1 GPIO20
Text Notes 900 1900 0 100 ~ 20
CC1 -> R1 5.1k -> GND ; CC2 -> R2 5.1k -> GND
Text Notes 900 2400 0 100 ~ 20
U2 AP2112K: +5V_SYS IN -> +3V3 OUT -> ESP32 pin 2
Text Notes 900 2800 0 100 ~ 20
U1 GPIO5 -> U3 SN74AHCT1G125 -> R7 330R -> J2 DATA
Text Notes 900 3200 0 100 ~ 20
U3 VCC=+5V_SYS ; /OE=GND ; J2 = +5V / DATA / GND
Text Notes 900 3600 0 100 ~ 20
C7 1000uF from +5V_SYS to GND near J2
Text Notes 900 4000 0 100 ~ 20
EN: R5 10k to 3V3, C6 1uF to GND, RESET switch to GND
Text Notes 900 4400 0 100 ~ 20
GPIO0: R6 10k to 3V3, BOOT switch to GND
Text Notes 900 4800 0 100 ~ 20
J3 Qwiic: GND / 3V3 / GPIO8 SDA / GPIO9 SCL
Text Notes 900 5200 0 100 ~ 20
GPIO48 -> R8 1k -> D1 green LED -> GND
$EndSCHEMATC
