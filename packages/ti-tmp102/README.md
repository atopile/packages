# Texas Instruments TMP102 12-bit I2C Temperature Sensor

Driver for the [TI TMP102](https://www.ti.com/product/TMP102), a popular ultra-small digital temperature sensor with I2C interface.

## Features

- 12-bit resolution, 0.0625°C per LSB
- ±0.5°C accuracy (−25°C to +85°C)
- Range: −40°C to +125°C
- Supply: 1.4V to 3.6V, <10µA quiescent
- Programmable alert threshold
- 4 selectable I2C addresses
- SOT-563 package (1.6 × 1.2 mm)

## Usage

```ato
import ElectricPower
import I2C
from "atopile/ti-tmp102/ti-tmp102.ato" import TI_TMP102

module MyDesign:
    power = new ElectricPower
    i2c = new I2C

    temp = new TI_TMP102
    power ~ temp.power
    i2c ~ temp.i2c

    # ADD0 to GND → 0x48
    temp.addressor.address_lines[0].line ~ power.lv
```

## I2C Address

| ADD0 | Address |
|------|---------|
| GND  | 0x48    |
| VCC  | 0x49    |
| SDA  | 0x4A    |
| SCL  | 0x4B    |

## License

MIT
