# Raspberry Pi Compute Module 5 (CM5)

## Usage

```ato
from "atopile/cm5.ato" import CM5

module App:
    # Components
    cm5 = new CM5

    # Interfaces
    power_5v = new Power

    # Connect Power
    power_5v ~ cm5.power_5v

```

## Overview

This package provides the necessary components and interfaces to integrate the Raspberry Pi Compute Module 5 into your hardware designs using atopile.

## Features

- **Processor:** High-performance ARM Cortex CPU
- **Memory:** LPDDR4X SDRAM options
- **Connectivity:** PCIe, Gigabit Ethernet, USB 3.0/2.0, MIPI DSI/CSI, etc.
- **Storage:** eMMC flash options or interface for external storage
- **Power Interface:** Requires 5V input, minimum 2A (ideally 3A+)
- **GPIO Pins:** Extensive General Purpose Input/Output pins
- **Wireless:** Optional Wi-Fi and Bluetooth module

## Example Layout

(Consider adding an image or link to an example carrier board layout if available)

### Layout Notes

- Basic functional layout provided

## Documentation & Resources

- [Official Raspberry Pi CM5 Documentation](https://www.raspberrypi.com/documentation/) (Update with direct link when available)
- [CM5 Datasheet](https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf)
- [CM5 Design Guide](link-to-design-guide) (Add link when available)

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This `rpi-cm5` atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
