# Maxim DS1841 Logarithmic Digital Potentiometer (22 kΩ → 3.7 kΩ, I²C)

The **Maxim Integrated DS1841** is a 128-step (7-bit) *logarithmic* digital potentiometer
with an integrated EEPROM for non-volatile wiper storage.  The resistance curve is
approximately logarithmic, spanning 22 kΩ at the top end (RH) down to ≈ 3.7 kΩ at the
wiper’s lower extreme.  Control is provided over an I²C bus, making the DS1841 a handy
drop-in replacement for multi-turn trim-pots in gain and bias networks, especially when
fine resolution is required at the low-resistance end.

* **Resistance range:** 22 kΩ → 3.7 kΩ (log taper) across 128 positions
* **Non-volatile:** EEPROM stores the wiper setting for automatic recall
* **Supply voltage (VCC):** 2.7 V – 5.5 V
* **I²C address:** `0x28` – `0x2B` selectable via **A1:A0** pins
* **Package:** 10-pin TDFN-EP (3 × 3 mm)
* **LCSC ID:** **C7454008** (part `DS1841N+T&R`)

## Ato Module Exposed Interfaces

| Interface | Description |
|-----------|-------------|
| `power`   | Digital supply rail (**VCC/GND**) |
| `i2c`     | I²C control bus (Fast-mode supported) |
| `potentiometer_high`  | High terminal (**RH**) |
| `potentiometer_low`   | Low terminal / resistor ground (**RGND**) |
| `potentiometer_wiper` | Wiper terminal (**RW**) |

## Usage Example
```ato
import ElectricPower
import I2C
import Electrical

from "atopile/maxim-ds1841/maxim-ds1841.ato" import Maxim_DS1841

# Example MCU providing I²C bus and reading the wiper voltage with an ADC pin
module MCU:
    power = new ElectricPower
    i2c = new I2C
    adc_in = new Electrical

module Usage:
    """
    Minimal wiring for the Maxim DS1841 logarithmic digital potentiometer (22 kΩ to 3.7 kΩ) used as a programmable voltage divider.

    1. The potentiometer top end (`RH`) is tied to 3V3, bottom end (`RL`) to GND.
    2. The wiper (`RW`) is routed to an MCU ADC input so firmware can read the
       divided voltage and the DS3502 can trim it over I²C.
    3. Address pins `A1:A0` are left low which selects I²C address 0x28.
    """

    # MCU with I²C and ADC capabilities
    mcu = new MCU

    # DS1841 instance
    pot = new Maxim_DS1841

    # Shared 3 V3 rail
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I²C bus (Fast-mode, 400 kHz)
    i2c_bus = new I2C
    pot.i2c.address = 0x28  # A1=A0=0 on DS1841

    # Power distribution
    power_3v3 ~ mcu.power
    power_3v3 ~ pot.power

    # Connect I²C
    i2c_bus ~ mcu.i2c
    i2c_bus ~ pot.i2c

```

## License

Released under the [MIT License](https://opensource.org/license/mit).
