# NXP PCF8574 8-bit I2C GPIO Expander

A comprehensive driver for the NXP PCF8574 remote 8-bit I/O expander for I2C-bus with interrupt. This package provides a complete atopile implementation for GPIO expansion applications.

## Features

- **8-bit I/O Expansion**: Quasi-bidirectional I/O pins that can be configured as inputs or outputs
- **I2C Interface**: Standard I2C bus communication up to 400 kHz (Fast-mode)
- **Interrupt Output**: Active-low open-drain interrupt for input change detection
- **Address Selection**: 3 hardware address pins (A0, A1, A2) allowing up to 8 devices on one bus
- **Wide Supply Range**: Operates from 2.5V to 6.0V
- **Low Power**: 10µA maximum standby current

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import I2C
import ElectricPower
import ElectricLogic
from "atopile/nxp-pcf8574/nxp-pcf8574.ato" import NXP_PCF8574

module Usage:
    """
    Minimal usage example for nxp-pcf8574.
    Demonstrates how to use the PCF8574 8-bit I2C GPIO expander
    in a typical application with TSSOP-16 package.
    """

    # Power supply
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # I2C bus for communication
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz

    # GPIO expander
    gpio_expander = new NXP_PCF8574

    # Connect power
    power_3v3 ~ gpio_expander.power

    # Connect I2C bus
    i2c_bus ~ gpio_expander.i2c

    # Set I2C address (using hardware address pins)
    # Address will be 0x20 + value set by A2:A1:A0 pins
    assert gpio_expander.i2c.address within 0x20 +/- 0%  # Default address with A2=A1=A0=0

    # Optional: Connect interrupt line for input change notifications
    interrupt_signal = new ElectricLogic
    interrupt_signal ~ gpio_expander.interrupt

    # Example: Connect some GPIO pins for typical usage
    led_outputs = new ElectricLogic[4]    # First 4 pins as outputs for LEDs
    button_inputs = new ElectricLogic[4]  # Last 4 pins as inputs for buttons

    # Connect the GPIO pins directly
    led_outputs[0] ~ gpio_expander.gpio[0]
    led_outputs[1] ~ gpio_expander.gpio[1]
    led_outputs[2] ~ gpio_expander.gpio[2]
    led_outputs[3] ~ gpio_expander.gpio[3]

    button_inputs[0] ~ gpio_expander.gpio[4]
    button_inputs[1] ~ gpio_expander.gpio[5]
    button_inputs[2] ~ gpio_expander.gpio[6]
    button_inputs[3] ~ gpio_expander.gpio[7]

```

## Key Interfaces

### Power Supply
- **Voltage**: 2.5V to 6.0V (3.3V or 5V typical)
- **Current**: Low power operation (~10µA standby)
- **Decoupling**: 100nF capacitor included

### I2C Communication
- **Address Range**: 0x20 to 0x27 (set by A2:A1:A0 pins)
- **Speed**: Up to 400kHz (Fast-mode I2C)
- **Pull-up Resistors**: 10kΩ included (optional - may be external)

### GPIO Pins
- **Count**: 8 quasi-bidirectional I/O pins (P0-P7)
- **Configuration**: Software configurable as inputs or outputs
- **Input**: Weak internal pull-up (100µA) when configured as input
- **Output**: 25mA sink capability per pin (80mA total package)
- **Voltage**: 5.5V tolerant when VDD < 5.5V

### Interrupt
- **Type**: Active-low open-drain output
- **Function**: Asserted when any input changes state
- **Usage**: Allows microcontroller to detect input changes without polling

## Address Selection

The PCF8574 supports 8 different I2C addresses using the A2, A1, A0 pins:

| A2 | A1 | A0 | Address |
|----|----|----|---------|
| 0  | 0  | 0  | 0x20    |
| 0  | 0  | 1  | 0x21    |
| 0  | 1  | 0  | 0x22    |
| 0  | 1  | 1  | 0x23    |
| 1  | 0  | 0  | 0x24    |
| 1  | 0  | 1  | 0x25    |
| 1  | 1  | 0  | 0x26    |
| 1  | 1  | 1  | 0x27    |

Note: PCF8574A has addresses 0x38-0x3F, allowing up to 16 devices total on one bus.

## Applications

- **LED Matrix Control**: Drive LED displays and indicators
- **Keypad Scanning**: Read button matrices and keypads
- **Relay Control**: Control multiple relays for switching applications
- **Sensor Interfacing**: Expand digital I/O for sensors and actuators
- **Level Shifting**: Interface between different logic levels
- **Industrial Control**: PLC and automation applications

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
