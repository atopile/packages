# SD and microSD Card Slots

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
import Resistor
import Capacitor
import SPI
import ElectricLogic
import ElectricPower

from "atopile/sd-card/main.ato" import SDCardAssemblyWithRemovableMicroSDWithSPI
from "atopile/esp32/esp32_c3.ato" import ESP32_C3_WROOM

module Usage:
    mcu = new ESP32_C3_WROOM
    sd_card = new SDCardAssemblyWithRemovableMicroSDWithSPI

    # Connect micro SD Card
    sd_card.spi ~ mcu.spi[0]
    sd_card.spi_cs ~ mcu.gpios[17]
    sd_card.power ~ mcu.power

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
