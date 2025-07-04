# Sensirion SGP40 VOC Sensor

A minimal driver for the Sensirion **SGP40** indoor air-quality (VOC) sensor.

## Features

- I²C interface (fixed address `0x59`)
- 1.71 – 3.6 V supply range
- Automatic on-chip humidity compensation (handled in firmware)
- Example wiring with 3 V3 rail and bus pull-ups

## Usage

```ato
import I2C
import ElectricPower
from "atopile/sensirion-sgp40" import Sensirion_SGP40_driver

module MyBoard:
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    i2c = new I2C
    sensor = new Sensirion_SGP40_driver

    sensor.power ~ power_3v3
    sensor.i2c ~ i2c
```

## License

MIT
