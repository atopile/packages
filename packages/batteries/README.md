# Batteries

## Usage

```ato
from "atopile/batteries/eemb_battery_lp402535.ato" import LP402535_driver

import ElectricPower

module App:
    battery = new LP402535_driver
    connector = new MOLEX_532610271_package

    power_battery = new ElectricPower
    power_battery ~ battery.power
    power_battery.hv ~ connector.2
    power_battery.lv ~ connector.1
```

## Overview

This package contains the base for various battery types and battery implementations.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
