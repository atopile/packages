# Texas Instruments INA228 85V, 20-bit I2C Current/Power Monitor

The INA228 is a high-precision current and power monitoring IC from Texas Instruments featuring a 20-bit delta-sigma ADC. It supports both high-side and low-side current sensing with up to 85V common-mode voltage capability, making it suitable for a wide range of power monitoring applications.

## Key Features

- **20-bit ADC**: Ultra-precise current and power measurements
- **Wide common-mode voltage range**: -0.3V to +85V
- **High accuracy**: Better than 0.1% current measurement accuracy
- **I2C interface**: 2.94 MHz high-speed I2C with 16 selectable addresses
- **Integrated temperature sensor**: ±1°C accuracy for thermal monitoring
- **Configurable alerts**: Fast 75µs alert response time
- **Low power consumption**: 2.7V to 5.5V supply voltage range

## Applications

- Battery management systems
- Power supply monitoring
- Motor control systems
- Solar panel monitoring
- Industrial automation
- Automotive power monitoring

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower
import I2C
from "ti-ina228.ato" import TI_INA228

module Usage:
    """
    Minimal usage example for TI INA228 power monitor.

    This example shows how to connect the INA228 to monitor current through
    a shunt resistor with 3.3V supply and I2C interface.
    """

    # Power rails
    supply = new ElectricPower
    load = new ElectricPower
    supply.voltage = 3.3V +/- 5%

    # I2C bus
    i2c = new I2C

    # Current monitor
    current_monitor = new TI_INA228
    current_monitor.max_current = 2A
    current_monitor.power ~ supply

    # Wiring - bridge the current monitor in the power path
    supply ~> current_monitor ~> load
    current_monitor.i2c ~ i2c

    # I2C address configuration
    # INA228 supports 16 addresses (0x40-0x4F) based on A0/A1 connections:
    # A0, A1 can each connect to: GND=0, VS=1, SDA=2, SCL=3
    # Address = 0x40 + (A1_config << 2) + (A0_config << 1)
    # Examples:
    # - A0=GND, A1=GND: 0x40 (both pins to ground)
    # - A0=VS,  A1=GND: 0x42 (A0 to supply, A1 to ground)
    # - A0=SDA, A1=SCL: 0x4E (A0 to SDA, A1 to SCL)
    current_monitor.i2c.address = 0x40  # A0=GND, A1=GND configuration
```

## Interface Details

### Power Supply
- **Voltage Range**: 2.7V to 5.5V
- **Current Consumption**: Low power operation
- **Decoupling**: 100nF capacitor included in design

### I2C Configuration
- **Address Range**: 0x40 to 0x4F (16 addresses)
- **Default Address**: 0x40 (A0 and A1 both connected to GND)
- **Speed**: Up to 2.94 MHz
- **Pull-up Resistors**: Required (typically 4.7kΩ)
- **Address Configuration**: A0 and A1 can each connect to GND, VS, SDA, or SCL
- **Address Formula**: `0x40 + (A1_config << 2) + (A0_config << 1)`
  - GND = 0, VS = 1, SDA = 2, SCL = 3

### Current Sensing
- **Shunt Voltage Range**: ±163.84mV or ±40.96mV
- **Common-Mode Voltage**: Up to 85V
- **Resolution**: 2.5µA to 10µA per LSB depending on range

## Pin Configuration

The INA228 uses address pins A0 and A1 to configure the I2C address:
- Connect to GND, VS, SDA, or SCL for different address combinations
- Default (both pins to GND) gives address 0x40
- Supports up to 16 devices on the same I2C bus

### Address Configuration Examples
| A1 Connection | A0 Connection | Address |
|---------------|---------------|---------|
| GND          | GND          | 0x40    |
| GND          | VS           | 0x42    |
| GND          | SDA          | 0x44    |
| GND          | SCL          | 0x46    |
| VS           | GND          | 0x48    |
| VS           | VS           | 0x4A    |
| SDA          | SDA          | 0x4C    |
| SCL          | SCL          | 0x4F    |

## Usage Pattern

The INA228 module supports the bridge pattern, allowing it to be inserted inline in power paths:

```ato
supply ~> current_monitor ~> load
```

This automatically connects the shunt resistor in series with the current path and configures the voltage monitoring.

## PCB Layout Guidelines

For optimal performance, follow these PCB layout recommendations:

1. **Shunt Resistor Placement**: Keep the shunt resistor as close as possible to the INpos/INneg pins
2. **Kelvin Connections**: Use separate traces for the current path and voltage sensing to minimize errors
3. **Noise Reduction**: Route INpos/INneg traces away from switching circuits and high-frequency signals
4. **Ground Plane**: Use a solid ground plane underneath the INA228 and shunt resistor
5. **Decoupling**: Place the decoupling capacitor within 5mm of the VS pin
6. **High-Voltage Isolation**: For voltages above 30V, ensure proper isolation between VBUS and low-voltage circuits

## Safety Considerations

⚠️ **HIGH VOLTAGE WARNING**: The VBUS pin can handle voltages up to 85V. When designing circuits with voltages above 30V:

- Follow IPC-2221 spacing requirements for high-voltage traces
- Use appropriate creepage and clearance distances
- Consider using conformal coating for additional protection
- Ensure proper isolation between high-voltage and low-voltage sections
- Test thoroughly before handling or powering the circuit

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
