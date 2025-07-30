# Analog Devices ADBMS6822 Dual isoSPI Transceiver

The ADBMS6822 is a dual-channel isolated SPI (isoSPI) transceiver that enables robust, isolated communication for battery management systems. It provides galvanic isolation while maintaining high-speed SPI communication over differential twisted pair cables.

## Features

- Dual independent isoSPI channels
- Configurable as SPI controller or peripheral
- Supports up to 1 Mbps data rate
- Low Power Communication Mode (LPCM)
- Wide supply voltage range: 1.7V to 5.5V (SPI), 3.0V to 5.5V (isoSPI)
- Built-in bypass capacitors for all power rails
- Configurable SPI phase/polarity, transceiver modes, and timeout settings

## Usage

```ato
import ElectricPower, SPI from "generics/interfaces.ato"
from "adi-adbms6822/adi-adbms6822.ato" import ADI_ADBMS6822

module BatteryManagementSystem:
    # Power supplies
    power_3v3 = new ElectricPower
    power_5v = new ElectricPower

    # Create dual isoSPI transceiver
    iso_transceiver = new ADI_ADBMS6822

    # Connect power supplies
    power_3v3 ~ iso_transceiver.vdds_spi_power  # SPI side power
    power_5v ~ iso_transceiver.vdd_iso_spi_power # isoSPI side power
    power_5v ~ iso_transceiver.vp_power          # High voltage supply

    # Connect SPI interface to microcontroller
    micro.spi[0] ~ iso_transceiver.spi[0]
    micro.gpio[0] ~ iso_transceiver.spi_cs[0]

    # Configure as SPI peripheral (default)
    # The configurator automatically sets up the mode pins

    # Connect isoSPI to battery modules
    iso_transceiver.isospi_ports[0] ~ battery_module_1.isospi
    iso_transceiver.isospi_ports[1] ~ battery_module_2.isospi
```

## Configuration

The ADBMS6822 configuration is handled by the `ADI_ADBMS6822_Configurator` which sets up the mode pins based on template parameters:

- **SPI Mode**: Controller or Peripheral mode for each channel
- **PHAPOL**: SPI clock phase and polarity settings
- **XCVRMD**: Transceiver mode (bidirectional standard, fast, etc.)
- **RTO**: Low Power Communication Mode timeout period

Default configuration is dual peripheral mode with standard settings. Modify the configurator template parameters to change the configuration.

## Pin Connections

The module automatically handles:
- Power supply bypass capacitors (1µF on each rail)
- Configuration resistors for mode selection
- isoSPI differential pair connections
- SPI interface connections

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
