# Electrical Net Summary

## USB-C input
- J1 VBUS pins -> F1 -> +5V_SYS
- J1 GND + shell -> GND
- J1 CC1 -> R1 5.1k -> GND
- J1 CC2 -> R2 5.1k -> GND
- J1 D- -> U4 ESD -> R3 22R -> ESP32 GPIO19
- J1 D+ -> U4 ESD -> R4 22R -> ESP32 GPIO20

## 3.3V logic
- +5V_SYS -> U2 AP2112K IN
- U2 OUT -> +3V3
- C4 10uF and C1/C2 decoupling around regulator/module
- ESP32 EN -> R5 10k to 3V3; C6 1uF to GND; SW1 to GND
- ESP32 GPIO0 -> R6 10k to 3V3; SW2 to GND

## LED path
- +5V_SYS -> J2 pin 1
- GND -> J2 pin 3
- +5V_SYS -> C7 1000uF -> GND near J2
- ESP32 GPIO5 -> U3 input
- U3 powered from +5V_SYS, OE tied low
- U3 output -> R7 330R -> J2 pin 2

## Expansion
- J3: GND, +3V3, GPIO8 SDA, GPIO9 SCL

## Status
- GPIO48 -> R8 1k -> D1 green LED -> GND
