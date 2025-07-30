# Analog Devices ADBMS6830 16-Channel Battery Stack Monitor

The ADBMS6830 is a highly integrated battery stack monitor that measures up to 16 series-connected battery cells with 16-bit ADC resolution. It features cell balancing, temperature monitoring, and both SPI and isoSPI communication interfaces for robust battery management systems.

## Features

- Monitors up to 16 series-connected battery cells
- 16-bit ADC with < 1mV total measurement error
- Cell voltage range: 1.8V to 4.25V per cell
- Total stack voltage: 11V to 85V
- Integrated passive cell balancing (200mA max discharge current per channel)
- 9 general-purpose I/O pins for temperature/voltage monitoring
- Dual communication interfaces: SPI and isoSPI
- Built-in 5V regulator with external NPN transistor
- Comprehensive filtering and protection circuits

## Usage

```ato
import ElectricPower, SPI, DifferentialPair from "generics/interfaces.ato"
from "adi-adbms6830/adi-adbms6830.ato" import ADI_ADBMS6830

module BatteryModule:
    # Create 16-cell battery monitor
    battery_monitor = new ADI_ADBMS6830

    # Connect battery cells (16s configuration)
    cells = new ElectricPower[16]
    cells[0] ~ battery_monitor.cell_stack[0]
    cells[1] ~ battery_monitor.cell_stack[1]
    # ... connect remaining cells 2-15

    # Connect main battery voltage (kelvin connection)
    battery_monitor.vbat.hv ~ cells[15].hv
    battery_monitor.vbat.lv ~ cells[0].lv

    # SPI communication to microcontroller
    micro.spi[0] ~ battery_monitor.spi
    micro.gpio[0] ~ battery_monitor.spi_cs

    # Configure for SPI mode (pull ISOMD low)
    battery_monitor.isomd.line ~ micro.gnd

    # Connect temperature sensors to GPIO pins
    temp_sensors = new Thermistor[4]
    temp_sensors[0].signal ~ battery_monitor.gpios[0]
    temp_sensors[0].reference ~ battery_monitor.vref2  # Use VREF2 for biasing
    # ... connect remaining temp sensors 1-3

    # For daisy-chain configuration using isoSPI
    battery_monitor.iso_a_external ~ next_module.iso_b_external
```

## Key Interfaces

### Power Supply
- **vbat**: Main battery stack voltage (11V to 85V)
- **vreg**: 5V regulated output (generated internally)
- **vref2**: 3V reference output for thermistor biasing

### Cell Monitoring
- **cell_stack[16]**: Individual cell voltage connections
- **cell_sense_inputs[16]**: Differential sense inputs (connected internally)
- **cell_balance_inputs[16]**: Cell balancing connections

### Communication
- **spi**: Standard SPI interface (when ISOMD = 0)
- **iso_a_external/iso_b_external**: isoSPI interfaces for daisy-chain
- **isomd**: Mode select pin (0 = SPI, 1 = isoSPI)

### GPIO
- **gpios[9]**: General-purpose I/O for temperature/voltage monitoring

## Built-in Protection

The module includes:
- Input RC filters on all cell sense inputs (200�/10nF)
- Cell balancing current limiting resistors
- isoSPI isolation capacitors (22nF, >100V rating)
- Power supply filtering and bypass capacitors
- Specialized C9N filter for improved noise rejection

## Cell Balancing

Passive cell balancing is implemented with:
- Maximum discharge current: 200mA per channel
- Balance resistors sized appropriately for thermal management
- Independent control of each balance channel

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
