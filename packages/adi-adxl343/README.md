# Analog Devices ADXL343 3-Axis Accelerometer

Driver for the [ADXL343](https://www.analog.com/en/products/adxl343.html), a low-power 3-axis MEMS accelerometer with I2C and SPI interfaces. Drop-in compatible with the ADXL345 — same pinout, lower cost.

## Features

- ±2g, ±4g, ±8g, ±16g selectable range
- 13-bit resolution at ±16g
- I2C and SPI interfaces
- Two interrupt outputs (motion, free-fall, tap detection)
- Ultra-low power: 23µA in measurement mode
- Supply: 2.0V to 3.6V (VS), 1.7V to 3.6V (VDDIO)
- LGA-14 package

## Usage

```ato
import ElectricPower
import I2C
from "atopile/adi-adxl343/adi-adxl343.ato" import ADI_ADXL343

module MyDesign:
    power = new ElectricPower
    i2c = new I2C

    accel = new ADI_ADXL343
    power ~ accel.power_vs
    power ~ accel.power_io
    i2c ~ accel.i2c
```

I2C address is fixed at 0x53 (SDO tied to GND).

## License

MIT
