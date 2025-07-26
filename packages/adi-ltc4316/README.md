# Analog Devices LTC4316 I2C Address Translator

The LTC4316 is a specialized I2C address translator that enables resolving address conflicts between I2C devices on the same bus. It provides "on-the-fly" address translation using XOR bitwise operations, allowing multiple devices with identical hardwired addresses to coexist on the same I2C bus.

## Key Features

- **Address Translation**: XOR-based address remapping for I2C slave devices (up to 127 translations)
- **Wide Voltage Range**: 2.25V to 5.5V operation
- **Conflict Resolution**: Enables devices with identical addresses to coexist
- **External Configuration**: Address translation controlled by external resistors
- **Ready Signal**: Open-drain output indicating device operational status
- **Enable Control**: Active-high enable pin for translation control
- **Built-in Pull-ups**: Integrated I2C pull-up resistors (4.7kΩ) for both input/output buses
- **Mixed Voltage Support**: Input and output I2C buses can operate at different voltages

## Usage

```ato
#pragma experiment("TRAITS")
import Resistor
import I2C
import ElectricPower
import ElectricLogic

from "adi-ltc4316.ato" import ADI_LTC4316

module Usage:
    """
    Minimal usage example for adi-ltc4316.
    Shows how to use the LTC4316 I2C address translator to resolve address conflicts.
    """

    # I2C address translator
    translator = new ADI_LTC4316

    # Power supply
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%
    power_3v3 ~ translator.power

    # I2C buses
    i2c_input = new I2C
    i2c_output = new I2C

    # Connect I2C buses
    i2c_input ~ translator.i2c_in
    i2c_output ~ translator.i2c_out

    # Enable the translator - permanently enable with pull-up
    enable_pullup = new Resistor
    enable_pullup.resistance = 10kohm +/- 5%
    enable_pullup.package = "0402"
    translator.enable.line ~ enable_pullup.unnamed[0]
    power_3v3.hv ~ enable_pullup.unnamed[1]

    # Configure address translation with pull-up/down resistors
    # XOR configuration resistors determine address translation
    power_3v3 ~ translator.xor_high.reference
    power_3v3 ~ translator.xor_low.reference

    xor_high_pullup = new Resistor
    xor_high_pullup.resistance = 10kohm +/- 5%
    xor_high_pullup.package = "0402"
    translator.xor_high.line ~ xor_high_pullup.unnamed[0]
    power_3v3.hv ~ xor_high_pullup.unnamed[1]

    xor_low_pulldown = new Resistor
    xor_low_pulldown.resistance = 10kohm +/- 5%
    xor_low_pulldown.package = "0402"
    translator.xor_low.line ~ xor_low_pulldown.unnamed[0]
    power_3v3.lv ~ xor_low_pulldown.unnamed[1]
```

## Address Translation Configuration

The LTC4316 performs address translation using XOR logic on address bits A4, A5, and A6. The translation is configured using external resistors on the XORH and XORL pins:

- **XORH (pin 2)**: Controls translation of address bits A5 and A6
- **XORL (pin 3)**: Controls translation of address bit A4

Pull the pins high (via pull-up resistor) or low (via pull-down resistor) to configure the desired address translation.

## Important Notes

- **Clock Stretching**: The LTC4316 does NOT support I2C clock stretching
- **Incompatible Devices**: Not compatible with devices that use clock stretching (e.g., BNO055)
- **Reset Required**: Address translation changes require ENABLE pin toggle to take effect
- **Configuration Latching**: Address translation settings are latched on ENABLE rising edge
- **Voltage Compatibility**: Supports mixed voltage I2C buses (input and output can be different voltages)
- **Ground Reference**: Both input and output I2C buses must share the same ground reference
- **Current Consumption**: ~2mA when enabled, ~800µA when disabled
- **Built-in Components**: Module includes all necessary pull-up resistors and decoupling capacitors

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
