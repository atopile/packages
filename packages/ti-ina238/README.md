# Texas Instruments INA238 Current, Voltage & Power Monitor

`ti-ina238` provides a ready-to-use atopile driver for the [INA238](https://www.ti.com/product/INA238) precision digital power monitor.

The module exposes an I²C interface and bridges a high-side shunt resistor to measure the current flowing from **power_in** to **power_out** while reporting shunt/bus voltage and calculated power.

## Features

- High-accuracy, bidirectional current sensing (±80 mV shunt drop full-scale)
- 16-bit Δ-Σ ADC with programmable conversion time / averaging
- Operates from 2.7 V – 5.5 V supply, common-mode up to 85 V
- ALERT interrupt pin for over-limit events
- Two address pins → 4 selectable I²C addresses (0x40–0x43)
- Comes with on-board decoupling and configurable external shunt

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "ti-ina238.ato" import TI_INA238_driver

module Usage:
    supply = new ElectricPower
    load   = new ElectricPower
    supply.voltage = 12V +/- 5%

    i2c = new I2C

    sensor = new TI_INA238_driver
    sensor.max_current = 5A

    supply ~> sensor ~> load
    sensor.i2c ~ i2c
    sensor.i2c.address = 0x40
```

## License

This package is released under the MIT license. See the [LICENSE](../../LICENSE) file for details.
