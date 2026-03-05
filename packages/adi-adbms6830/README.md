# Analog Devices ADBMS6830 Battery Monitor

16-channel cell monitor with 16 cell sense and bleed inputs, SPI and isoSPI interfaces, and 10 GPIOs.

For a guide on getting started with this chip checkout: https://blog.atopile.io/p/getting-started-with-adbms6830

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

from "atopile/adi-adbms6830/adi-adbms6830.ato" import ADI_ADBMS6830

import ElectricPower
import SPI

module Example:
    adbms6830 = new ADI_ADBMS6830

    # Power
    vbat = new ElectricPower
    assert vbat.voltage within 16V to 85V
    vbat ~ adbms6830.vbat

    # Cell connections
    cells = new ElectricPower[16]
    cells[0] ~ adbms6830.cell_stack[0]
    cells[1] ~ adbms6830.cell_stack[1]
    # ... connect remaining cells

    # SPI interface (active when ISOMD is low)
    spi = new SPI
    spi ~ adbms6830.spi
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
