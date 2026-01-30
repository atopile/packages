# Microchip MCP3421 18-bit, Single-Channel I²C ADC

The Microchip MCP3421 is an 18-bit, single-channel analog-to-digital converter with an I²C interface, internal 2.048V reference, and up to 240 SPS sampling rate. It features delta-sigma conversion technology with low noise and high accuracy, operating from 2.7V to 5.5V supply voltage.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Imports ---
import ElectricPower
import I2C

from "atopile/microchip-mcp3421/microchip-mcp3421.ato" import Microchip_MCP3421

module Usage:
    """
    Minimal usage example for microchip-mcp3421.
    Demonstrates connecting power and I2C to the MCP3421 18-bit ADC.
    """

    # --- Power supply ---
    power = new ElectricPower
    power.voltage = 3.3V +/- 5%

    # --- I2C bus ---
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # --- ADC instance ---
    adc = new Microchip_MCP3421

    # --- Connections ---
    power ~ adc.power
    i2c_bus ~ adc.i2c

    # --- Differential analog input example ---
    # Connect positive and negative inputs for true differential measurement
    # For single-ended, connect negative input to ground
    # adc.analog_input.p connects to your positive signal
    # adc.analog_input.n connects to your negative signal or ground

    # --- I2C address is fixed at 0x68 ---
    # No address configuration needed

```

## Features

- **18-bit resolution**: High precision analog-to-digital conversion
- **Differential input**: True differential analog input pair (p/n)
- **Internal 2.048V reference**: No external reference required
- **I²C interface**: Fixed address 0x68, up to 400kHz
- **Low power**: Typical 120µA supply current
- **Wide supply range**: 2.7V to 5.5V operation


## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
