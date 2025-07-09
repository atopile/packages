# Sensirion SHTC3 Temperature & Humidity Sensor

`C194656` • ±2 % RH, ±0.2 °C digital humidity and temperature sensor in a compact 2 × 2 mm DFN.

The **SHTC3** is an ultra-low-power humidity & temperature sensor optimised for battery-powered applications. It communicates via an I²C bus (fixed 7-bit address **0x70**) and operates from **1.62 V – 3.6 V**.

This package wraps the raw JLCPCB part into an easy-to-use Atopile module, complete with power-rail modelling, on-board I²C pull-ups and the required 100 nF decoupling capacitor.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower, I2C
from "sensirion-shtc3.ato" import Sensirion_SHTC3

module Example:
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    i2c = new I2C

    sensor = new Sensirion_SHTC3
    power_3v3 ~ sensor.power
    power_3v3 ~ i2c.scl.reference; power_3v3 ~ i2c.sda.reference
    i2c ~ sensor.i2c
```

## License

MIT © atopile
