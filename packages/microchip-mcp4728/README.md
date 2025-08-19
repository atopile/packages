# Microchip MCP4728 Quad 12-bit DAC with EEPROM

The MCP4728 is a quad channel, 12-bit voltage output Digital-to-Analog Converter (DAC) with non-volatile memory (EEPROM) and an I2C interface. The device includes an on-chip voltage reference and supports individual channel configuration with the ability to store settings to EEPROM for power-on defaults.

## Features

- 4 independent 12-bit DAC channels
- I2C interface (7-bit addressing)
- Non-volatile EEPROM for storing DAC settings
- Internal voltage reference (2.048V) with external reference option
- Individual channel power-down modes
- Ready/Busy status output
- Load DAC (LDAC) input for simultaneous output updates
- 2.7V to 5.5V supply voltage range
- MSOP-10 package

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C

from "atopile/microchip-mcp4728/microchip-mcp4728.ato" import Microchip_MCP4728

module Usage:
    """
    Minimal usage example for microchip-mcp4728.
    Demonstrates basic connection of the MCP4728 quad DAC with I2C interface and power supply.
    """

    # Create instance of the MCP4728 DAC
    dac = new Microchip_MCP4728

    # Power supply (3.3V typical)
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # I2C bus
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz
    i2c_bus.address = 0x60  # Default address

    # Connect interfaces
    power_3v3 ~ dac.power
    i2c_bus ~ dac.i2c

    # Optional: Set LDAC pin low to enable immediate DAC output updates
    # dac.ldac.line can be connected to a GPIO or tied to ground

    # Optional: Monitor ready/busy status
    # dac.ready.line can be connected to a GPIO for status monitoring

    # DAC outputs are available on:
    # dac.vouta.line - Channel A output
    # dac.voutb.line - Channel B output
    # dac.voutc.line - Channel C output
    # dac.voutd.line - Channel D output

```

## I2C Address Configuration

The MCP4728 supports 8 different I2C addresses (0x60 to 0x67) that are factory programmed. The address selection depends on the device ordering code:
- MCP4728A0: 0x60
- MCP4728A1: 0x61
- MCP4728A2: 0x62
- MCP4728A3: 0x63
- MCP4728A4: 0x64
- MCP4728A5: 0x65
- MCP4728A6: 0x66
- MCP4728A7: 0x67

## Pin Description

- **VDD**: Power supply positive (2.7V to 5.5V)
- **VSS**: Power supply negative (ground)
- **SCL**: I2C clock line
- **SDA**: I2C data line
- **nLDAC**: Load DAC input (active low)
- **RDY/nBSY**: Ready/Busy status output (active low when busy)
- **VOUTA**: DAC Channel A output
- **VOUTB**: DAC Channel B output
- **VOUTC**: DAC Channel C output
- **VOUTD**: DAC Channel D output

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
