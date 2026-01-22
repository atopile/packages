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
#pragma experiment("BRIDGE_CONNECT")
import Ethernet
import Capacitor

from "atopile/pjrc-teensy-4-1/pjrc-teensy-4-1.ato" import PJRC_Teensy_4_1

from "parts/WIZNET_J1B1211CCD/WIZNET_J1B1211CCD.ato" import WIZNET_J1B1211CCD_package

from "atopile/usb-connectors/usb-connectors.ato" import USB2_0TypeCHorizontalConnector
from "atopile/buttons/buttons.ato" import VerticalButton

module Usage:
    """
    Usage example for the PJRC Teensy 4.1
    """
    # --- Components ---
    teensy = new PJRC_Teensy_4_1
    usb_connector = new USB2_0TypeCHorizontalConnector
    ethernet_connector = new EthernetConnector
    power_button = new VerticalButton
    program_button = new VerticalButton

    # --- Connections ---
    teensy.usb_device ~ usb_connector.usb
    teensy.ethernet ~ ethernet_connector.ethernet

    teensy.on_off.line ~> power_button ~> teensy.on_off.reference.lv
    teensy.program.line ~> program_button ~> teensy.program.reference.lv

    # --- Net renaming ---
    teensy.usb_device.usb_if.d.p.line.override_net_name = "USB_P"
    teensy.usb_device.usb_if.d.n.line.override_net_name = "USB_N"
    teensy.usb_host.usb_if.d.p.line.override_net_name = "USB_HOST_P"
    teensy.usb_host.usb_if.d.n.line.override_net_name = "USB_HOST_N"
    teensy.ethernet.pairs[0].p.line.override_net_name = "ETH_RX_P"
    teensy.ethernet.pairs[0].n.line.override_net_name = "ETH_RX_N"
    teensy.ethernet.pairs[1].p.line.override_net_name = "ETH_TX_P"
    teensy.ethernet.pairs[1].n.line.override_net_name = "ETH_TX_N"

module EthernetConnector:
    """
    RJ45 connector with Ethernet interface
    """
    # --- Components ---
    connector = new WIZNET_J1B1211CCD_package
    capacitor = new Capacitor
    assert capacitor.capacitance within 100nF +/- 10%
    capacitor.package = "0402"

    # --- External interfaces ---
    ethernet = new Ethernet

    # --- internal connections ---
    connector.9 ~ connector.8
    connector.8 ~> capacitor ~> connector.2
    connector.8 ~> capacitor ~> connector.5

    # --- package connections ---
    ethernet.pairs[0].n.line ~ connector.6
    ethernet.pairs[0].p.line ~ connector.4
    ethernet.pairs[1].n.line ~ connector.3
    ethernet.pairs[1].p.line ~ connector.1

    ethernet.led_speed.line ~ connector.10 # LLEDpos
    ethernet.led_speed.reference.lv ~ connector.9 # LLEDneg

    ethernet.led_speed.reference.lv ~ connector.14 # GND
    ethernet.led_speed.reference.lv ~ connector.13 # GND

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
