# Mounting Holes

Various mounting holes.

Supported Sizes:

- M2
- M2_5
- M3
- M4
- M5
- M6
- M8

Supported Pad Types:

- NoPad
- Pad
- Pad_TopOnly
- Pad_Via

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
from "MountingHole.py" import MountingHole

module Usage:
    """
    Example of using mounting holes
    """

    m2_with_pad = new MountingHole<metric_screw_size="M3", pad_type="Pad">
    m6_no_pad = new MountingHole<metric_screw_size="M6", pad_type="NoPad">
    m3_top_pad = new MountingHole<metric_screw_size="M3", pad_type="Pad_TopOnly">
    m4_pad_with_vias = new MountingHole<metric_screw_size="M4", pad_type="Pad_Via">

    m2_with_pad.contact ~ m3_top_pad.contact
    m3_top_pad.contact ~ m4_pad_with_vias.contact
    # m6_no_pad has no contact

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
