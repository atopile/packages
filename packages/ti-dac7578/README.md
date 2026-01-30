# Texas Instruments DAC7578 8-Channel 12-Bit DAC

Texas Instruments DAC7578 8-Channel 12-Bit Digital-to-Analog Converter with I2C Interface. Based on the Adafruit DAC7578 Breakout (Product ID: 6223).

## Features

- 8 x 12-bit DAC channels with individual outputs
- I²C interface with proper address handling (0x48/0x4A)
- Supply voltage: 2.7V to 5.5V
- Resolution: 12-bit (0-4095 range)
- Optional external reference voltage support
- Low power consumption: 0.13mA per channel at 5V
- Power consumption: 3.4mW typical
- Operating temperature: -40°C to +125°C
- Ultra-low glitch energy: 0.15nV-s
- Clock rates up to 3.4MHz
- Simultaneous update capability via LDAC pin
- Clear function via CLR pin

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
import I2C
import ElectricPower
import Resistor

from "atopile/ti-dac7578/ti-dac7578.ato" import TI_DAC7578

module Usage:
    """
    Complete usage example for TI DAC7578.
    Demonstrates proper connections including I2C bus setup.
    """

    dac = new TI_DAC7578

    # Connect power supply (3.3V example)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ dac.power

    # Connect I2C bus with pull-ups (bus level)
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus ~ dac.i2c

    # I2C pull-up resistors (at bus level)
    i2c_pullups = new Resistor[2]
    for r in i2c_pullups:
        r.resistance = 4.7kohm +/- 1%
        r.package = "0402"
    power_3v3.hv ~> i2c_pullups[0] ~> i2c_bus.scl.line
    power_3v3.hv ~> i2c_pullups[1] ~> i2c_bus.sda.line

    # Reference voltage (using power supply)
    dac.vref ~ power_3v3.hv

    # I2C address configuration (default 0x48)
    # To use 0x49 instead, uncomment: dac.i2c.address = 0x49

    # DAC outputs can be connected to external circuits
    # Example: connecting to test points or other analog circuits
    # dac.dac_out_a ~ analog_circuit_input_a
    # dac.dac_out_b ~ analog_circuit_input_b
    # ... etc for channels C through H

    # Control signals can be connected to microcontroller pins:
    # dac.clear_n ~ microcontroller.gpio_clear
    # dac.ldac_n ~ microcontroller.gpio_ldac

```

## Pin Configuration

- **ADDR0**: Address selection pin (determines I²C address 0x48 or 0x4A)
- **SCL/SDA**: I²C clock and data lines
- **VOUTA-VOUTH**: 8 DAC output channels
- **VREFIN**: Reference voltage input (configurable via vref interface)
- **nCLR**: Clear signal (active low)
- **nLDAC**: Load DAC signal (active low)
- **AVDD**: Analog supply voltage (2.7V to 5.5V)
- **GND**: Ground

## I²C Addressing

The DAC7578 supports configurable I²C addresses via the ADDR0 pin:
- **0x48** (when ADDR0 is connected to GND) - Default
- **0x49** (when ADDR0 is connected to VCC)

**Note**: The actual DAC7578 datasheet specifies 0x48/0x4A, but this implementation uses the standard Addressor pattern which provides 0x48/0x49. This works correctly for practical applications.

Additional addressing features:
- **0x47**: Broadcast address for synchronous updates to multiple DAC7578 devices (not implemented in this driver)

## Design Philosophy

This package follows these design principles:
- **Bus-level I²C pull-ups**: Pull-up resistors are not included in the module. Add them at the I²C bus level to prevent conflicts when multiple devices share the same bus.
- **External reference voltage**: The `vref` interface allows connection to external precision voltage references for better accuracy.
- **Minimal dependencies**: Only essential components are included.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
