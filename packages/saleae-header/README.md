# Saleae Debug Header Connectors

Debug header configured for use with Saleae logic analyzers, includes interfaces for signals (io + gnd) as well as support for monitoring buses like I2C and SPI. Monitor your SPI bus as easily as `saleae.spi ~ micro.spi`!

Features:
- **SaleaeHeaderVertical**: Single vertical header for connection via harness
- **SaleaeHeaderRightAngle_x**: Right-angle headers for direct connection to Saleae(x=1,2,4)
- **Built-in protection**: 1kΩ series resistors on all signal lines
- **Bus monitoring**: Easy connection to I2C, SPI, and other digital signals

![Saleae Debug Header](https://firebasestorage.googleapis.com/v0/b/atopile.appspot.com/o/saleae-debug-header.png?alt=media&token=84e11ffe-b67d-438b-ae7e-e35b59780a78 "Saleae Debug Header")

## Usage

```ato
from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderVertical, SaleaeHeaderRightAngle_2
import ElectricSignal,SPI,I2C

module Usage:
    # Example signals of interest
    spi = new SPI
    spi_cs = new ElectricSignal
    i2c = new I2C

    # Single vertical header for connection with Saleae through harness
    harness_saleae_debug_header = new SaleaeHeaderVertical

    spi.sclk ~ harness_saleae_debug_header.channels[0]
    spi.miso ~ harness_saleae_debug_header.channels[1]
    spi.mosi ~ harness_saleae_debug_header.channels[2]
    spi_cs ~ harness_saleae_debug_header.channels[3]

    # Double right angle female header for direct connection to Saleae Logic 8/16
    direct_saleae_interface = new SaleaeHeaderRightAngle_2

    spi ~ direct_saleae_interface.headers[0].spi

    i2c ~ direct_saleae_interface.headers[1].i2c
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
