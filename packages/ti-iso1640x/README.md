# TI ISO1640 I2C Isolator

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import I2C
import Power

from "atopile/ti-iso1640x/ti-iso1640.ato" import Texas_Instruments_ISO1640_driver
from "atopile/ti-iso1640x/parts/Texas_Instruments_ISO1640QDWRQ1/Texas_Instruments_ISO1640QDWRQ1.ato" import Texas_Instruments_ISO1640QDWRQ1_package
from "atopile/ti-iso1640x/parts/TEXAS_INSTRUMENTS_ISO1640BDR/TEXAS_INSTRUMENTS_ISO1640BDR.ato" import TEXAS_INSTRUMENTS_ISO1640BDR_package


module Micro:
    i2c = new I2C
    power = new Power

module Sensor:
    i2c = new I2C
    power = new Power

module Test:
    """
    Connect a microcontroller to a sensor via an I2C isolator
    """

    # Components
    micro = new Micro
    sensor = new Sensor
    isolator = new Texas_Instruments_ISO1640_driver

    # Power Rails
    power = new ElectricPower
    power_iso = new ElectricPower

    # Select Package
    # isolator.package -> Texas_Instruments_ISO1640QDWRQ1_package   #1500v
    isolator.package -> TEXAS_INSTRUMENTS_ISO1640BDR_package      #400v

    # Connections - isolator is 'bridgable'
    micro.i2c ~> isolator ~> sensor.i2c
    # alternative connection method:
    # micro.i2c ~> isolator.i2cs[0]
    #sensor.i2c ~> isolator.i2cs[1]

    # Power
    power ~ micro.power
    power ~ isolator.power_rails[0]

    # Isolated Power
    power_iso ~ sensor.power
    power_iso ~ isolator.power_rails[1]


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
