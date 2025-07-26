# NXP PCF8575 16-bit I2C GPIO Expander

A comprehensive driver for the NXP PCF8575 remote 16-bit I/O expander for I2C-bus with interrupt. This package provides a complete atopile implementation for GPIO expansion applications.

## Features

- **16-bit I/O Expansion**: Quasi-bidirectional I/O pins that can be configured as inputs or outputs
- **I2C Interface**: Standard I2C bus communication up to 400 kHz (Fast-mode)
- **Interrupt Output**: Active-low open-drain interrupt for input change detection
- **Address Selection**: 3 hardware address pins (A0, A1, A2) allowing up to 8 devices on one bus
- **Operating Range**: 4.5V to 5.5V supply voltage
- **Low Power**: 10µA maximum standby current


## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import I2C, ElectricPower, ElectricLogic
from "nxp-pcf8575.ato" import NXP_PCF8575

module Usage:
    """
    Minimal usage example for nxp-pcf8575.
    Demonstrates how to use the PCF8575 16-bit I2C GPIO expander
    in a typical application with SSOP-24 package.
    """

    # Power supply
    power_5v = new ElectricPower
    assert power_5v.voltage within 4.9V to 5.1V

    # I2C bus for communication
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz

    # GPIO expander
    gpio_expander = new NXP_PCF8575

    # Connect power
    power_5v ~ gpio_expander.power

    # Connect I2C bus
    i2c_bus ~ gpio_expander.i2c

    # Set I2C address (using hardware address pins)
    # Address will be 0x20 + value set by A2:A1:A0 pins
    assert gpio_expander.i2c.address is 0x20  # Default address with A2=A1=A0=0

    # Optional: Connect interrupt line for input change notifications
    interrupt_signal = new ElectricLogic
    interrupt_signal ~ gpio_expander.interrupt

    # Example: Connect GPIO pins for typical usage
    # Port 0 (first 8 pins) as outputs for LEDs
    led_outputs = new ElectricLogic[8]
    led_outputs[0] ~ gpio_expander.gpio[0]
    led_outputs[1] ~ gpio_expander.gpio[1]
    led_outputs[2] ~ gpio_expander.gpio[2]
    led_outputs[3] ~ gpio_expander.gpio[3]
    led_outputs[4] ~ gpio_expander.gpio[4]
    led_outputs[5] ~ gpio_expander.gpio[5]
    led_outputs[6] ~ gpio_expander.gpio[6]
    led_outputs[7] ~ gpio_expander.gpio[7]

    # Port 1 (second 8 pins) as inputs for buttons
    button_inputs = new ElectricLogic[8]
    button_inputs[0] ~ gpio_expander.gpio[8]
    button_inputs[1] ~ gpio_expander.gpio[9]
    button_inputs[2] ~ gpio_expander.gpio[10]
    button_inputs[3] ~ gpio_expander.gpio[11]
    button_inputs[4] ~ gpio_expander.gpio[12]
    button_inputs[5] ~ gpio_expander.gpio[13]
    button_inputs[6] ~ gpio_expander.gpio[14]
    button_inputs[7] ~ gpio_expander.gpio[15]
```

## Key Interfaces

### Power Supply
- **Voltage**: 4.5V to 5.5V (5V typical)
- **Current**: Low power operation (~10µA standby)
- **Decoupling**: 100nF capacitor included

### I2C Communication
- **Address Range**: 0x20 to 0x27 (set by A2:A1:A0 pins)
- **Speed**: Up to 400kHz (Fast-mode I2C)
- **Pull-up Resistors**: 10kΩ included (optional - may be external)

### GPIO Pins
- **Count**: 16 quasi-bidirectional I/O pins (2 ports of 8 pins each)
- **Port 0**: P00-P07 (maps to gpio[0:7])
- **Port 1**: P10-P17 (maps to gpio[8:15])
- **Configuration**: Software configurable as inputs or outputs
- **Input**: Weak internal pull-up when configured as input
- **Output**: 25mA sink capability per pin
- **Data Transfer**: 16-bit data must be transferred in pairs (even number of bytes)

### Interrupt
- **Type**: Active-low open-drain output
- **Function**: Asserted when any input changes state
- **Usage**: Allows microcontroller to detect input changes without polling

## Address Selection

The PCF8575 supports 8 different I2C addresses using the A2, A1, A0 pins:

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

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
