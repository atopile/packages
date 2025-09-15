# Raspberry Pi Compute Module 5 (CM5)

## Usage

```ato
from "atopile/rpi-cm5/rpi-cm5.ato" import RPI_CM5

from "atopile/usb-connectors/usb-connectors.ato" import USB2_0TypeCHorizontalConnector
from "atopile/rj45-connectors/rj45-connectors.ato" import RJ45_Horizontal_TH_Magnetics

module Usage:
    """Usage example for the Raspberry Pi CM5 module"""

    cm5 = new RPI_CM5

    # Connectors
    usbc_connector = new USB2_0TypeCHorizontalConnector
    rj45_connector = new RJ45_Horizontal_TH_Magnetics

    usbc_connector.usb ~ cm5.usb2
    usbc_connector.usb.usb_if.buspower ~ cm5.power_5v
    rj45_connector.ethernet ~ cm5.ethernet
```

## Overview

This package provides the necessary components and interfaces to integrate the Raspberry Pi Compute Module 5 into your hardware designs using atopile.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This `rpi-cm5` atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
