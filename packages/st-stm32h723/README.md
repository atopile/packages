# ST STM32H723 Cortex-M7 MCU (RMII, USB, I2C, SPI, UART)

High-performance Arm Cortex-M7 microcontroller up to 550 MHz with up to 1 MB Flash, 564 KB RAM, USB FS, multiple I2C/SPI/UART, and built-in Ethernet MAC. Includes RMII interface to connect an external PHY (e.g. Microchip LAN8742A).

- Datasheet: https://jlcpcb.com/api/file/downloadByFileSystemAccessId/8588886273382109184

## Usage

```ato
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
import ElectricLogic

from "st-stm32h723.ato" import ST_STM32H723
from "../microchip-lan8742a/microchip-lan8742a.ato" import Microchip_LAN8742A, RMII

module Usage:
    power_3v3 = new ElectricPower
    mcu = new ST_STM32H723
    phy = new Microchip_LAN8742A
    rmii = new RMII
    mdio = new I2C
    reset = new ElectricLogic

    power_3v3 ~ mcu.power_3v3
    power_3v3 ~ phy.power_3v3

    # USB PHY supply (3.3 V)
    mcu.power_usb ~ power_3v3

    rmii ~ mcu.rmii
    rmii ~ phy.rmii

    mdio ~ phy.mdio

    reset.reference ~ power_3v3
    reset.line ~ phy.reset.line
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the MIT License.
