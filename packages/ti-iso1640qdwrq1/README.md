# Texas Instruments ISO1640QDWRQ1 I2C Isolator

The ISO1640QDWRQ1 is a bidirectional I2C isolator that provides 1500V isolation between two I2C buses. It supports data rates up to 1MHz and operates with supply voltages from 2.25V to 5.5V on each side. This device is automotive qualified (AEC-Q100).

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import I2C
import ElectricPower

from "atopile/ti-iso1640qdwrq1/ti-iso1640qdwrq1.ato" import TI_ISO1640QDWRQ1

module Microcontroller:
    i2c = new I2C
    power = new ElectricPower

module Sensor:
    i2c = new I2C
    power = new ElectricPower

module Example:
    # Components
    micro = new Microcontroller
    sensor = new Sensor
    isolator = new TI_ISO1640QDWRQ1

    # Power Rails
    power_3v3 = new ElectricPower
    power_iso_3v3 = new ElectricPower

    # Set power rail voltages
    assert power_3v3.voltage within 3.3V +/- 5%
    assert power_iso_3v3.voltage within 3.3V +/- 5%

    # I2C frequency
    assert micro.i2c.frequency <= 400kHz
    assert sensor.i2c.frequency <= 400kHz

    # Connections - isolator is 'bridgable'
    micro.i2c ~> isolator ~> sensor.i2c

    # Power connections
    power_3v3 ~ micro.power
    power_3v3 ~ isolator.power_rails[0]

    # Isolated power
    power_iso_3v3 ~ sensor.power
    power_iso_3v3 ~ isolator.power_rails[1]
```

## Features

- 1500V isolation voltage
- Bidirectional I2C communication
- Data rates up to 1MHz
- Supply voltage range: 2.25V to 5.5V (each side)
- Hot-swap capability
- Automotive qualified (AEC-Q100)
- SOIC-16 package
- Built-in I2C pullup resistors (10kΩ 0402) on both sides
- Decoupling capacitors (100nF 0402) for stable operation

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
