# Microchip MCP9808 High-Precision Digital Temperature Sensor

High-precision digital temperature sensor with user-programmable temperature alerts and configurable I2C address. The MCP9808 provides ±0.25°C typical accuracy and multiple resolution options for precise temperature monitoring applications.

## Features

- **High Accuracy**: ±0.25°C (typical), ±1°C (maximum) from -40°C to +125°C
- **Selectable Resolution**: 0.5°C, 0.25°C, 0.125°C, or 0.0625°C (default)
- **Low Power**: 200µA typical operation, 0.1µA shutdown mode
- **Flexible Interface**: I2C with 8 possible addresses (0x18 to 0x1F)
- **Programmable Alerts**: Temperature alert output with user-configurable limits
- **Wide Supply Range**: 2.7V to 5.5V operation
- **Robust Operation**: -40°C to +125°C operating range

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
import I2C
import ElectricPower

from "atopile/microchip-mcp9808/microchip-mcp9808.ato" import Microchip_MCP9808


module Usage:
    """
    Minimal usage example for microchip-mcp9808.
    Shows basic connection of the MCP9808 temperature sensor with I2C and power interfaces.
    """

    sensor = new Microchip_MCP9808

    # External interfaces
    i2c = new I2C
    power = new ElectricPower

    # Connect all required interfaces
    i2c ~ sensor.i2c
    power ~ sensor.power

    # Set power supply voltage (example: 3.3V)
    assert power.voltage within 3.0V to 3.6V

    # Set I2C address to 0x1F (A2=1, A1=1, A0=1 - all address pins high)
    sensor.i2c.address = 0x1F

    # The alert output is available at sensor.alert if needed

```

## Pin Configuration

- **VDD**: Power supply (2.7V to 5.5V)
- **GND**: Ground
- **SDA**: I2C data line
- **SCL**: I2C clock line
- **Alert**: Temperature alert output (open-drain)
- **A0, A1, A2**: Address selection pins

## I2C Address Configuration

The MCP9808 supports 8 different I2C addresses (0x18 to 0x1F) configured using the A0, A1, and A2 pins:

| A2 | A1 | A0 | Address |
|----|----|----|---------|
| 0  | 0  | 0  | 0x18    |
| 0  | 0  | 1  | 0x19    |
| 0  | 1  | 0  | 0x1A    |
| 0  | 1  | 1  | 0x1B    |
| 1  | 0  | 0  | 0x1C    |
| 1  | 0  | 1  | 0x1D    |
| 1  | 1  | 0  | 0x1E    |
| 1  | 1  | 1  | 0x1F    |

Connect address pins to GND for logic 0 or VDD for logic 1.

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
