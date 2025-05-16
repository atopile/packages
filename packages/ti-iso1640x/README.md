# Raspberry Pi Compute Module 5 (CM5)

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import I2C
import Power

from "atopile/ti-iso1640x/ti-iso1640.ato" import Texas_Instruments_ISO1640_driver
from "atopile/ti-iso1640x/ti-iso1640.ato" import Texas_Instruments_ISO1640QDWRQ1_package
from "atopile/ti-iso1640x/ti-iso1640.ato" import Texas_Instruments_ISO1640BDR_package

module Micro:
    i2c = new I2C
    power = new Power

module Sensor:
    i2c = new I2C
    power = new Power

module App:
    """
    Connect a microcontroller to a sensor via an I2C isolator
    """

    # Components
    micro = new Micro
    sensor = new Sensor
    isolator = new Texas_Instruments_ISO1640_driver

    # Power Rails
    power = new Power
    power_iso = new Power

    # Select Package
    isolator.package -> Texas_Instruments_ISO1640QDWRQ1_package   #400V
    #isolator.package -> Texas_Instruments_ISO1640BDR_package      #1500V

    # Connections
    micro.i2c ~> isolator ~> sensor.i2c

```

## Overview

This package provides the necessary components and interfaces to integrate the Raspberry Pi Compute Module 5 into your hardware designs using atopile.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
