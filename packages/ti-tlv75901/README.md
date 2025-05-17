# Relays

Contains a DPDT relay (HFD4_5) with logic level driver circuit and LED indicator

## Usage

```ato

import ElectricPower

from "atopile/ti-tlv75901/ti-tlv75901.ato" import TLV75901_driver

module Test:
    # Create LDO
    ldo = new TLV75901_driver

    # Configure voltages
    ldo.v_in = 5V +/- 1%
    ldo.v_out = 3.3V +/- 3%

    # Create example power interfaces
    power_in = new ElectricPower
    power_out = new ElectricPower

    # Connect to regulator (bridge connect)
    power_in ~> ldo ~> power_out

    # Connect to regulator (Interfaces)
    power_in ~ ldo.power_in
    power_out ~ ldo.power_out

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
