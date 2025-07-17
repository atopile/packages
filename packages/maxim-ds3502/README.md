# Maxim DS3502 Digital Potentiometer (10 kΩ, I²C)

The **Maxim Integrated DS3502** is a 128-step (7-bit), non-volatile 10 kΩ digital
potentiometer controllable over an I²C bus.
It is ideal for replacing mechanical trim-pots in calibration and biasing applications.
The device integrates an EEPROM that stores the wiper position, allowing the resistance
setting to be automatically restored on power-up.

* **Resistance range:** 0 Ω – 10 kΩ in 128 equal steps (≈78 Ω/step)
* **Supply voltage (VCC):** 2.7 V – 5.5 V
  (analog **V+** pin supports 4.5 V – 15.5 V when biasing higher-voltage rails)
* **I²C address:** `0x28` – `0x2B` selectable via pins **A1:A0**
* **Low standby current:** 0.3 µA (typ.)
* **Package:** 10-pin µMAX / MSOP-10
* **Adafruit breakout:** Product ID [4286](https://www.adafruit.com/product/4286)

This package wraps the raw IC in a reusable Ato **module** that exposes:

| Interface | Description |
|-----------|-------------|
| `power`   | Digital supply rail (**VCC/GND**) |
| `i2c`     | I²C control bus (up to 400 kHz) |
| `potentiometer_high`  | High terminal (**RH**) |
| `potentiometer_low`   | Low terminal (**RL**) |
| `potentiometer_wiper` | Wiper terminal (**RW**) |

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower, I2C, Electrical
from "maxim-ds3502.ato" import Maxim_DS3502

module Demo:
    """DS3502 used as programmable divider between 3V3 and GND"""

    # Shared rail
    rail_3v3 = new ElectricPower
    rail_3v3.voltage = 3.3V +/- 5%

    # I²C bus @ 400 kHz, address 0x28 (A1=A0=0)
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus.address = 0x28

    # DS3502 instance
    pot = new Maxim_DS3502

    # Connect power and control
    rail_3v3 ~ pot.power
    i2c_bus  ~ pot.i2c

    # Wire RH to 3V3, RL to GND, take RW as output
    rail_3v3.hv ~ pot.potentiometer_high.line   # RH
    rail_3v3.lv ~ pot.potentiometer_low.line    # RL

    divider_out = new Electrical
    divider_out ~ pot.potentiometer_wiper.line  # RW
```

## LCSC Part Information

| Field | Value |
|-------|-------|
| **Manufacturer** | Maxim Integrated |
| **Part Number** | DS3502U+T&R |
| **Package** | µMAX-10 (MSOP-10) |
| **LCSC ID** | **C2649363** |

## License

Provided under the [MIT License](https://opensource.org/license/mit).
