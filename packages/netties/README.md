# Mounting Holes

Various mounting holes.

Supported widths:

SMD:

- 0.3mm
- 0.5mm

THT:

- 0.3mm
- 1.0mm

Supported pin counts:

- 2
- 3
- 4

Supported Pad Types:

- SMD
- THT

The connect_gnd parameter can be used to connect the power.lv Electricals together (default) instead of the power.hv Electricals.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower

from "atopile/netties/NetTie.py" import NetTie

module Usage:
    """
    Example of using netties
    """

    basic_nettie = new NetTie
    basic_nettie_hv_connect = new NetTie<connect_gnd=False>
    weird_nettie = new NetTie<width=1.0, pin_count=3, pad_type="THT">
    basic_thru_hole_nettie = new NetTie<width=0.3, pad_type="THT">
    basic_thru_hole_nettie_hv_connect = new NetTie<width=0.3, pad_type="THT", connect_gnd=False>

    power_a = new ElectricPower
    power_b = new ElectricPower
    power_c = new ElectricPower

    # bridge connect for netties with 2 'pins'
    power_a ~> basic_nettie ~> power_b
    power_a ~> basic_thru_hole_nettie ~> power_b

    # manual connect for netties with > 2 'pins'
    weird_nettie.power[0] ~ power_b
    weird_nettie.power[1] ~ power_a
    weird_nettie.power[2] ~ power_c

    # connect power.hv's together
    power_a ~> basic_nettie_hv_connect ~> power_b
    power_a ~> basic_thru_hole_nettie_hv_connect ~> power_b
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
