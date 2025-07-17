# AWINIC AW9523 GPIO Expander and LED Driver

The AWINIC AW9523 is a versatile 16-bit I2C GPIO expander and LED driver in a TQFN-24-EP package. It provides 16 configurable GPIO pins that can function as either digital inputs/outputs or PWM LED drivers with 256-step linear dimming capability.

## Key Features

- **16 GPIO pins** (2 ports of 8 pins each)
- **Flexible pin configuration**: Each pin can be configured as GPIO input/output or PWM LED driver
- **PWM LED driving**: 256-step linear constant-current dimming (up to 37mA per pin)
- **I2C interface**: Standard I2C communication with 4 configurable addresses (0x58-0x5B)
- **Interrupt capability**: Built-in interrupt controller for GPIO state changes
- **Wide supply range**: 2.5V to 5.5V operation
- **1.8V logic compatibility**
- **Maximum total power**: 3.2W across all pins

## Pin Configuration

The AW9523 has two 8-bit ports:
- **Port 0**: P0_0 to P0_7 (gpios[0] to gpios[7])
- **Port 1**: P1_0 to P1_7 (gpios[8] to gpios[15])

Each pin can be individually configured as:
- Digital input with optional interrupt
- Digital output
- PWM LED driver output

## I2C Addressing

The device supports 4 I2C addresses based on AD0 and AD1 pin states:

| AD1 | AD0 | Address |
|-----|-----|---------|
| 0   | 0   | 0x58    |
| 0   | 1   | 0x59    |
| 1   | 0   | 0x5A    |
| 1   | 1   | 0x5B    |

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic
import I2C

from "awinic-aw9523.ato" import Awinic_AW9523

module Usage:
    """
    Minimal usage example for `awinic-aw9523`.
    Demonstrates basic GPIO expander setup with I2C interface and power supply.
    """

    # --- Main component ---
    gpio_expander = new Awinic_AW9523

    # --- Power supply ---
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # --- I2C bus ---
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz +/- 50kHz

    # --- Connect interfaces ---
    power_3v3 ~ gpio_expander.power
    i2c_bus ~ gpio_expander.i2c

    # --- Set I2C address ---
    # Default address 0x58 (both AD0 and AD1 pulled low)
    # Address pins are automatically configured via addressor

    # --- Example GPIO usage ---
    # GPIO pins are available as gpio_expander.gpios[0] through gpio_expander.gpios[15]
    # These can be connected to LEDs, buttons, sensors, etc.

    # Example: Connect some GPIOs to external signals
    led_control = new ElectricLogic[4]
    button_input = new ElectricLogic[4]

    gpio_expander.gpios[0] ~ led_control[0]
    gpio_expander.gpios[1] ~ led_control[1]
    gpio_expander.gpios[2] ~ led_control[2]
    gpio_expander.gpios[3] ~ led_control[3]
    gpio_expander.gpios[8] ~ button_input[0]
    gpio_expander.gpios[9] ~ button_input[1]
    gpio_expander.gpios[10] ~ button_input[2]
    gpio_expander.gpios[11] ~ button_input[3]
```

## Important Notes

- **No internal pull-ups/pull-downs**: External resistors are required if pull-up or pull-down functionality is needed
- **LED driving**: When using constant-current LED mode, LEDs can be connected directly without current-limiting resistors
- **Interrupt capability**: The INTN pin provides interrupt functionality with 8μs deglitch
- **Power considerations**: Maximum 37mA per pin, 3.2W total power across all pins
- **Reset**: Active-low reset pin (RSTN) for device initialization

## Applications

- GPIO expansion for microcontrollers
- LED matrix control and dimming
- Keypad/button matrix scanning
- Sensor interface expansion
- General digital I/O expansion

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
