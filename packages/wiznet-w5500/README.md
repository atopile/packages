# Wiznet W5500 Ethernet Controller

The W5500 is a hardwired TCP/IP embedded Ethernet controller that enables easier internet connection for embedded systems. It supports SPI interface and includes 32KB internal memory buffer for Ethernet packet processing.

## Features

- Hardwired TCP/IP stack supporting TCP, UDP, ICMP, IPv4, ARP, IGMP, PPPoE protocols
- 32KB internal memory buffer for Ethernet packet processing
- SPI interface (up to 80MHz)
- Auto-negotiation (10/100 Mbps, Half/Full duplex)
- Auto MDI/MDIX
- 3.3V operation
- Integrated PHY and MAC
- 25MHz crystal oscillator (Yangxing Tech X322525MRB4SI)

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import ElectricLogic
import ElectricPower
import Ethernet
import SPI

from "atopile/wiznet-w5500/wiznet-w5500.ato" import Wiznet_W5500
from "atopile/rj45-connectors/rj45-connectors.ato" import RJ45_Horizontal_TH_Magnetics

module Usage:
    """
    Minimal usage example for wiznet-w5500.
    Shows how to connect the W5500 to an RJ45 connector with proper magnetics and termination.
    """

    # Power supply
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.15V to 3.45V

    # SPI bus
    spi_bus = new SPI

    # W5500 Ethernet controller
    w5500 = new Wiznet_W5500
    w5500.power ~ power_3v3
    w5500.spi ~ spi_bus

    # Connect chip select
    spi_cs = new ElectricLogic
    spi_cs.reference ~ power_3v3
    w5500.spi_cs ~ spi_cs

    # RJ45 connector with magnetics
    rj45 = new RJ45_Horizontal_TH_Magnetics
    rj45.ethernet ~ w5500.ethernet
    rj45.shield ~ power_3v3.lv

    # The ethernet interface exposes:
    # - w5500.ethernet.pairs[0] = TX differential pair (TXP/TXN)
    # - w5500.ethernet.pairs[1] = RX differential pair (RXP/RXN)
    # - w5500.ethernet.led_link = Link status LED
    # - w5500.ethernet.led_speed = Activity/Speed LED

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
