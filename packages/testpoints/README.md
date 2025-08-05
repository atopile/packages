# Test Points

Various testpoints.

Supported sizes:

- 1.0mm
- 1.5mm
- 2.0mm
- 2.5mm
- 3.0mm
- 4.0mm

Supported Pad Types:

- SMD
- THT

A json file with testpoint data is generated in `build/<build_name>/<build_name>.testpoints.json` when adding the `mfg-data` target.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
from "atopile/testpoints/TestPoint.py" import TestPoint

module Usage:
    """
    Example of using testpoints
    """

    basic_testpoint = new TestPoint
    basic_tht_testpoint = new TestPoint<pad_type="THT">
    big_smd_testpoint = new TestPoint<size=3.0, pad_type="SMD">
    medium_tht_testpoint = new TestPoint<size=2.5, pad_type="THT">
    square_smd_testpoint = new TestPoint<size=2.0, pad_shape="SQUARE", pad_type="SMD">

    basic_testpoint.contact ~ basic_tht_testpoint.contact
    big_smd_testpoint.contact ~ medium_tht_testpoint.contact
    basic_testpoint.contact ~ square_smd_testpoint.contact
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
