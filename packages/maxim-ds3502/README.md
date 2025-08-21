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
import ElectricPower
import I2C

from "atopile/maxim-ds3502/maxim-ds3502.ato" import Maxim_DS3502

module Usage:
    """
    Minimal wiring for the Maxim DS3502 (10 kΩ) used as a programmable voltage divider.

    1. The potentiometer top end (`RH`) is tied to 3V3, bottom end (`RL`) to GND.
    2. The wiper (`RW`) can be routed to an MCU ADC input so firmware can read the
       divided voltage and the DS3502 can trim it over I²C.
    3. Address pins `A1:A0` are left low which selects I²C address 0x28.
    """

    # DS3502 digital potentiometer
    pot = new Maxim_DS3502

    # Power supply (3.3V typical)
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ pot.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c.address = 0x28  # A1=A0=0 on DS3502
    i2c ~ pot.i2c

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
