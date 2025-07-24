# PJRC Teensy 4.1

The PJRC Teensy 4.1 is a microcontroller board based on the NXP MCU LPC5526.

- ARM Cortex-M7 at 600 MHz
- Float point math unit, 64 & 32 bits
- 7936K Flash, 1024K RAM (512K tightly coupled), 4K EEPROM (emulated)
- QSPI memory expansion, locations for 2 extra RAM or Flash chips
- USB device 480 Mbit/sec & USB host 480 Mbit/sec
- 55 digital input/output pins, 35 PWM output pins
- 18 analog input pins
- 8 serial, 3 SPI, 3 I2C ports
- 2 I2S/TDM and 1 S/PDIF digital audio port
- 3 CAN Bus (1 with CAN FD)
- 1 SDIO (4 bit) native SD Card port
- Ethernet 10/100 Mbit with DP83825 PHY
- 32 general purpose DMA channels
- Cryptographic Acceleration & Random Number Generator
- RTC for date/time
- Programmable FlexIO
- Pixel Processing Pipeline
- Peripheral cross triggering
- Power On/Off management

## Usage

```ato
from "atopile/pjrc-teensy_4_1/pjrc-teensy_4_1.ato" import PJRC_Teensy_4_1
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn

module Usage:
    """
    Usage example for the PJRC Teensy 4.1
    """
    # --- Components ---
    teensy = new PJRC_Teensy_4_1
    usb_connector = new USBCConn
    ethernet_connector = new EthernetConnector

    # --- Connections ---
    teensy.usb_device ~ usb_connector.usb2
    teensy.ethernet ~ ethernet_connector.ethernet
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
