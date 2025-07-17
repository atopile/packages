# Texas Instruments INA238 16-bit I2C Current/Power Monitor

The INA238 is a high-precision current and power monitoring IC from Texas Instruments featuring a 16-bit delta-sigma ADC. It supports bidirectional current sensing for monitoring the current flowing from power_in to power_out while reporting shunt/bus voltage and calculated power.

## Key Features

- **16-bit ADC**: High-precision current and power measurements
- **Bidirectional current sensing**: ±80mV shunt drop full-scale
- **Wide operating range**: 2.7V to 5.5V supply
- **I2C interface**: Up to 3.4 MHz I2C-compatible interface with 4 selectable addresses
- **Configurable alerts**: Open-drain ALERT pin for over-limit conditions
- **Low power consumption**: Ideal for battery-powered applications
- **Built-in I2C pull-ups**: 10kΩ resistors included on SCL and SDA lines

## Applications

- Battery monitoring and management
- Power supply monitoring
- Motor current sensing
- Solar panel monitoring
- DC/DC converter efficiency measurement
- Load monitoring in embedded systems

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower
import I2C
from "ti-ina238.ato" import TI_INA238

module Usage:
    """
    Minimal usage example for TI INA238 power monitor.

    This example shows how to connect the INA238 to monitor current through
    a shunt resistor with 3.3V supply and I2C interface.
    """

    # Power rails
    supply = new ElectricPower
    load = new ElectricPower
    supply.voltage = 3.3V +/- 5%

    # I2C bus
    i2c = new I2C

    # Current monitor
    current_monitor = new TI_INA238
    current_monitor.max_current = 2A
    current_monitor.power ~ supply

    # Wiring - bridge the current monitor in the power path
    supply ~> current_monitor ~> load
    current_monitor.i2c ~ i2c

    # I2C address configuration
    # INA238 supports 4 addresses (0x40-0x43) based on A0/A1 connections:
    # - A0=GND, A1=GND: 0x40 (default)
    # - A0=VS,  A1=GND: 0x41
    # - A0=GND, A1=VS:  0x42
    # - A0=VS,  A1=VS:  0x43
    current_monitor.i2c.address = 0x40  # A0=GND, A1=GND configuration
```

## Interface Details

### Power Supply
- **Voltage Range**: 2.7V to 5.5V
- **Current Consumption**: Low power operation
- **Decoupling**: 100nF capacitor included in design

### I2C Configuration
- **Address Range**: 0x40 to 0x43 (4 addresses)
- **Default Address**: 0x40 (A0 and A1 both connected to GND)
- **Speed**: Up to 3.4 MHz I2C-compatible interface
- **Pull-up Resistors**: 10kΩ included on SCL and SDA lines
- **Address Configuration**: A0 and A1 pins can be connected to GND or VS
- **Address Formula**: Base address 0x40 + address pin configuration

### Current Sensing
- **Shunt Voltage Range**: ±80mV full-scale
- **Shunt Resistor**: Automatically sized based on max_current parameter
- **Package**: Default 1206 size for adequate power dissipation
- **Measurement Mode**: Bidirectional current sensing

### Alert Function
- **ALERT Pin**: Open-drain output with 10kΩ pull-up included
- **Configurable Limits**: Programmable for various conditions
- **Response Time**: Fast interrupt notification

## Pin Configuration

The INA238 uses address pins A0 and A1 to configure the I2C address:
- Connect to GND or VS for different address combinations
- Default (both pins to GND) gives address 0x40
- Supports up to 4 devices on the same I2C bus

### Address Configuration Table
| A1 Connection | A0 Connection | Address |
|---------------|---------------|---------|
| GND          | GND          | 0x40    |
| GND          | VS           | 0x41    |
| VS           | GND          | 0x42    |
| VS           | VS           | 0x43    |

## Usage Pattern

The INA238 module supports the bridge pattern, allowing it to be inserted inline in power paths:

```ato
supply ~> current_monitor ~> load
```

This automatically connects the shunt resistor in series with the current path and configures the voltage monitoring.

## PCB Layout Guidelines

For optimal performance, follow these PCB layout recommendations:

1. **Shunt Resistor Placement**: Keep the shunt resistor as close as possible to the INpos/INneg pins
2. **Kelvin Connections**: Use separate traces for the current path and voltage sensing to minimize errors
3. **Noise Reduction**: Route INpos/INneg traces away from switching circuits and high-frequency signals
4. **Ground Plane**: Use a solid ground plane underneath the INA238 and shunt resistor
5. **Decoupling**: Place the decoupling capacitor within 5mm of the VS pin

## Technical Specifications

- **Resolution**: 16-bit delta-sigma ADC
- **Conversion Time**: Programmable from 50µs to 4.156ms
- **Temperature Range**: -40°C to +125°C
- **Package**: VSSOP-10

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
