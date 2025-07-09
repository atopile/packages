# Microchip MCP23017 – 16-bit I²C GPIO Expander

This package provides an Atopile driver for the **MCP23017** 16-bit GPIO expander from Microchip Technology (LCSC part **C629439**).

## Usage

```ato
import I2C
import ElectricPower

from "atopile/microchip-mcp23017/microchip-mcp23017.ato" import MCP23017_driver

module MCU:
    power = new ElectricPower
    i2c = new I2C

module TopLevel:
    mcu = new MCU
    expander = new MCP23017_driver

    # 3.3 V rail shared between MCU & expander
    rail = new ElectricPower
    rail.voltage = 3.3V
    rail ~ mcu.power
    rail ~ expander.power

    # I²C bus
    mcu.i2c ~ expander.i2c

    # Optional: set desired I²C address (0x20–0x27)
    expander.i2c.address = 0x20
```

## Contributing

Pull requests are welcome!  Please run `ato build` on the `example` target and ensure CI passes before opening a PR.

## License

MIT License © 2025 Atopile Contributors 