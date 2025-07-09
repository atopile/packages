# Raspberry Pi Compute Module 5 (CM5)

## Usage

```ato
from "atopile/rpi-cm5/cm5.ato" import CM5

module App:
    # Components
    cm5 = new CM5

    # Interfaces
    power_5v = new Power
    i2c = new I2C

    # Connect Power
    power_5v ~ cm5.power_5v
    i2c ~ cm5.i2c[0]

```

## Overview

This package provides the necessary components and interfaces to integrate the Raspberry Pi Compute Module 5 into your hardware designs using atopile.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This `rpi-cm5` atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
