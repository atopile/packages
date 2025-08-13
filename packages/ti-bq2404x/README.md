# BQ2404XDSQR 1A 1S Battery Charger

Input Voltage: 4.45V - 6.45V
Charge termination Voltage: 4.20V/4.35V

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
from "atopile/ti-bq2404x/ti-bq2404x.ato" import BQ24040DSQR

module Usage:
    charger = new BQ24040DSQR
    power_in = new ElectricPower
    power_batt = new ElectricPower
    power_in ~> charger ~> power_batt
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
