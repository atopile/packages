# Texas Instruments OPT3001 Ambient Light Sensor

Driver for the [TI OPT3001](https://www.ti.com/product/OPT3001), a precision ambient light sensor with I2C interface and spectral response matched to the human eye.

## Features

- 23-bit effective dynamic range: 0.01 to 83865 lux
- Matched to human-eye spectral response (rejects IR/UV)
- Supply: 1.6V to 3.6V
- 4 selectable I2C addresses (0x44–0x47)
- Programmable interrupt (threshold comparator)
- USON-6 package (2.0 × 2.0 mm)

## Usage

```ato
import ElectricPower
import I2C
from "atopile/ti-opt3001/ti-opt3001.ato" import TI_OPT3001

module MyDesign:
    power = new ElectricPower
    i2c = new I2C

    sensor = new TI_OPT3001
    power ~ sensor.power
    i2c ~ sensor.i2c

    # ADDR to GND → 0x44
    sensor.addressor.address_lines[0].line ~ power.lv
```

## I2C Address

| ADDR | Address |
|------|---------|
| GND  | 0x44    |
| VDD  | 0x45    |
| SDA  | 0x46    |
| SCL  | 0x47    |

## License

MIT
