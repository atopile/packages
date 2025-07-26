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
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower, I2C, Electrical
from "maxim-ds1841.ato" import Maxim_DS1841

module Demo:
    # 3 V3 rail
    rail_3v3 = new ElectricPower
    rail_3v3.voltage = 3.3V +/- 5%

    # I²C bus @ 400 kHz, address 0x28 (A1=A0=0)
    bus = new I2C
    bus.frequency = 400kHz
    bus.address = 0x28

    pot = new Maxim_DS1841

    rail_3v3 ~ pot.power
    bus     ~ pot.i2c

    # Divider configuration: RH = 3 V3, RGND = GND, RW = output
    rail_3v3.hv ~ pot.potentiometer_high.line   # RH
    rail_3v3.lv ~ pot.potentiometer_low.line    # RGND

    v_out = new Electrical
    v_out ~ pot.potentiometer_wiper.line        # RW
```

## License

Released under the [MIT License](https://opensource.org/license/mit).
