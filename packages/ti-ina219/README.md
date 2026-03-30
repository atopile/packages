# Texas Instruments INA219 26V 12-bit I2C Current/Power Monitor

Driver for the [TI INA219](https://www.ti.com/product/INA219) — a popular bidirectional current and power monitoring IC with I²C interface and up to 26V common-mode voltage range.

## Features

- 12-bit ADC: 4µV shunt voltage resolution, 4mV bus voltage resolution
- Common-mode range: −0.3V to +26V
- Programmable shunt voltage range: ±40mV, ±80mV, ±160mV, ±320mV
- Supply voltage: 3V to 5.5V
- 4 selectable I2C addresses (0x40, 0x41, 0x44, 0x45)
- Inline high-side current sensing with configurable shunt resistor
- Decoupling capacitor and I²C pull-ups included

## Usage

```ato
import ElectricPower
import I2C
from "atopile/ti-ina219/ti-ina219.ato" import TI_INA219

module MyDesign:
    power_3v3 = new ElectricPower
    power_rail_in = new ElectricPower
    power_rail_out = new ElectricPower
    i2c = new I2C

    monitor = new TI_INA219

    # Power the INA219 from 3.3V
    power_3v3 ~ monitor.power

    # I²C bus
    power_3v3 ~ i2c.scl.reference
    power_3v3 ~ i2c.sda.reference
    i2c ~ monitor.i2c

    # Address 0x40: tie both address pins to GND
    monitor.a0_addr.line ~ power_3v3.lv
    monitor.a1_addr.line ~ power_3v3.lv

    # Insert inline on the rail to monitor (up to 1A)
    monitor.max_current = 1A
    power_rail_in ~ monitor.power_in
    monitor.power_out ~ power_rail_out
```

## I2C Address Selection

| A1  | A0  | Address |
|-----|-----|---------|
| GND | GND | 0x40    |
| GND | VS  | 0x41    |
| VS  | GND | 0x44    |
| VS  | VS  | 0x45    |

## Contributing

Contributions welcome via pull requests on the GitHub repository.

## License

MIT License
