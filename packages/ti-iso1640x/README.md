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
    isolator1 = new TEXAS_INSTRUMENTS_ISO1640BDR_driver # 400V
    # isolator1 = new TEXAS_INSTRUMENTS_ISO1640QDWRQ1_driver # 1500V

    # Power Rails
    power = new ElectricPower
    power_iso = new ElectricPower

    # Connections - isolator is 'bridgable'
    micro.i2c ~> isolator1 ~> sensor.i2c

    # Power
    power ~ micro.power
    power ~ isolator1.power_rails[0]

    # Isolated Power
    power_iso ~ sensor.power
    power_iso ~ isolator1.power_rails[1]



```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
