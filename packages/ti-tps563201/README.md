# TI TPS563201 Buck Converter

- Vin: 4.5V - 17V
- Vout: 0.76V - 7V
- Iout: up to 3A

## Usage

```ato

import I2C
import Power

from "atopile/ti-tps563201/ti-tps563201.ato" import Texas_Instruments_TPS563201DDCR_driver

module Test:
    # Create regulator
    regulators = new Texas_Instruments_TPS563201DDCR_driver

    # Configure Output Voltage
    regulators[0].v_out = 1.8V +/- 5%

    # Example Interfaces
    power_12v = new Power
    power_1v8 = new Power

    # Connect up
    power_12v ~> regulator ~> power_1v8

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
