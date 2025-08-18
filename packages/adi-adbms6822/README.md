# ADI ADBMS6822 Dual isoSPI Transceiver

The ADI ADBMS6822 is a dual isoSPI transceiver IC designed for isolated SPI communication in battery management systems and other high-voltage applications. This package provides a complete driver module with configurable SPI modes, power management, and dual differential isoSPI interfaces.

## Key Features

- Dual SPI interfaces (configurable as controller or peripheral)
- Dual isoSPI differential interfaces for isolated communication
- Multiple power rails with wide voltage ranges (1.7V-30V depending on rail)
- Configurable SPI clock phase/polarity, transceiver modes, and timeout settings
- Low Power Communication Mode (LPCM) with wake-up and interrupt signaling
- Built-in bypass capacitors and power decoupling

## Usage

```ato
import DifferentialPair, ElectricPower

from "atopile/pjrc-teensy-4-1/pjrc-teensy_4_1.ato" import PJRC_Teensy_4_1
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn
from "atopile/saleae-header/saleae-header.ato" import SaleaeHeaderRightAngle_2
from "atopile/adi-adbms6822/adi-adbms6822.ato" import ADI_ADBMS6822

module Usage:

    teensy = new PJRC_Teensy_4_1
    adbms6822 = new ADI_ADBMS6822
    usb_c_connector = new USBCConn

    # --- External Interfaces ---
    power_5v = new ElectricPower
    """
    Main power rail for the Teensy and ADBMS6822.
    """

    # --- Power Connections ---
    adbms6822.vdds_spi_power ~ power_5v
    adbms6822.vdd_iso_spi_power ~ power_5v
    adbms6822.vp_power ~ power_5v

    teensy.power ~ power_5v

    # --- SPI Interface Connections ---
    # Connect SPI buses to microcontroller
    teensy.spi[0] ~ adbms6822.spi[0]
    teensy.gpio[0] ~ adbms6822.spi_cs[0]

    teensy.spi[1] ~ adbms6822.spi[1]
    teensy.gpio[1] ~ adbms6822.spi_cs[1]

    # --- Saleae Debug Header Connections ---
    saleae_spi_interface = new SaleaeHeaderRightAngle_2

    # Spi 0
    saleae_spi_interface.headers[0].spi ~ adbms6822.spi[0]
    saleae_spi_interface.headers[0].spi_cs ~ adbms6822.spi_cs[0]

    # Spi 1
    saleae_spi_interface.headers[1].spi ~ adbms6822.spi[1]
    saleae_spi_interface.headers[1].spi_cs ~ adbms6822.spi_cs[1]
```

## Power Requirements

The ADBMS6822 requires three power supply rails:

- **vdds_spi_power**: 1.7V to 5.5V - Powers the SPI interface logic
- **vdd_iso_spi_power**: 3.0V to 5.5V - Powers the isoSPI interface
- **vp_power**: 3.0V to 30V - High voltage supply for Low Power Communication Mode

All power rails are marked as required and include built-in bypass capacitors.

## Configuration

The module includes automatic configuration through the `ADI_ADBMS6822_Configurator` which sets up:
- SPI mode selection (controller/peripheral)
- Clock phase and polarity settings
- Transceiver operating modes
- LPCM timeout periods

Configuration is done via resistor dividers on dedicated configuration pins.

## Interfaces

- **spi[2]**: Dual SPI interfaces
- **spi_cs[2]**: Chip select signals for each SPI interface
- **isospi_ports[2]**: Differential pair interfaces for isolated communication
- **wake_1/2**: Wake-up signaling for low power mode
- **intr_1/2**: Interrupt outputs for status indication

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
