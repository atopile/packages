# Relays

Contains a DPDT relay (HFD4_5) with logic level driver circuit and LED indicator

## Usage

```ato

import ElectricPower

from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import BYYXXS_2WR2
from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import _B2405_package
from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import _B2409_package
from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import _B2424_package
from "atopile/ylptech-byyxx/ylptech-byyxx.ato" import _B0505_package

module Test:

    # Create 4 regulators, each with a different package
    regulators = new BYYXXS_2WR2[4]
    regulators[0].package -> _B2405_package
    # regulators[1].package -> _B2409_package # currently missing lcsc data :(
    regulators[2].package -> _B2424_package
    regulators[3].package -> _B0505_package

    # Create power interfaces
    power_in = new ElectricPower
    power_out = new ElectricPower

    # Example connection
    power_in ~> regulators[0] ~> power_out

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
