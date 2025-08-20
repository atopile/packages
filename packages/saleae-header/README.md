# Debug Header for Saleae Logic Analyzers

Features:
- **SaleaeHeaderVertical**: Single vertical header for connection via harness
- **SaleaeHeaderRightAngle_x**: Right-angle headers for direct connection to Saleae(x=1,2,4)
- **Built-in protection**: 1kΩ series resistors on all signal lines
- **Bus monitoring**: Easy connection to I2C, SPI, and other digital signals

## SaleaeHeaderRightAngle_2
![Saleae Header Example](https://github.com/atopile/packages/blob/main/packages/saleae-header/saleae_header_example.png?raw=true)

## SaleaeHeaderVertical
![Saleae Header Example](https://github.com/atopile/packages/blob/main/packages/saleae-header/vertical_example.png?raw=true)

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")

from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderVertical
from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderRightAngle_2
import ElectricSignal,SPI,I2C

module Usage:
    # Example signals of interest
    spi = new SPI
    spi_cs = new ElectricSignal
    i2c = new I2C
    example_signals = new ElectricSignal[4]

    # Double right angle female header for direct connection to Saleae Logic 8/16
    direct_saleae_interface = new SaleaeHeaderRightAngle_2

    spi ~ direct_saleae_interface.headers[0].spi
    spi_cs ~ direct_saleae_interface.headers[0].spi_cs

    i2c ~ direct_saleae_interface.headers[1].i2c

    # Single vertical header for connection with Saleae through harness
    harness_saleae_debug_header = new SaleaeHeaderVertical

    example_signals[0] ~ harness_saleae_debug_header.channels[0]
    example_signals[1] ~ harness_saleae_debug_header.channels[1]
    example_signals[2] ~ harness_saleae_debug_header.channels[2]
    example_signals[3] ~ harness_saleae_debug_header.channels[3]

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
