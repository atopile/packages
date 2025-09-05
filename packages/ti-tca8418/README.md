# Texas Instruments TCA8418 Keypad Matrix Scanner and GPIO Expander

The TCA8418 is a versatile I2C-controlled keypad matrix scanner and GPIO expander that supports up to 80 switches in a matrix configuration. This atopile package provides a complete driver module with integrated decoupling capacitors and I2C pull-up resistors.

## Features

- 18 total GPIO pins (10 columns, 8 rows)
- Supports up to 80 switches in matrix configuration
- Integrated debounce functionality (50μs debounce time)
- 10-element event queue for key presses and releases
- Fixed I2C address: 0x34 (7-bit)
- Low power consumption: 3μA standby current
- Interrupt output (active low, open drain)
- Operating voltage: 1.8V to 3.6V

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import I2C
import ElectricPower

from "atopile/ti-tca8418/ti-tca8418.ato" import TI_TCA8418

module Usage:
    """
    Minimal usage example for TI TCA8418 keypad matrix scanner and GPIO expander.
    Demonstrates basic connections for I2C and power supply.
    """

    # Create TCA8418 instance
    keypad_controller = new TI_TCA8418

    # Create I2C bus
    i2c_bus = new I2C

    # Create power supply
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%

    # Connect interfaces
    i2c_bus ~ keypad_controller.i2c
    power_3v3 ~ keypad_controller.power

    # I2C address is automatically set to 0x34 (fixed)

    # GPIO row pins are available as keypad_controller.gpio_rows[0] through gpio_rows[7]
    # GPIO column pins are available as keypad_controller.gpio_cols[0] through gpio_cols[9]
    # Interrupt pin is available as keypad_controller.interrupt

```

## Pin Configuration

The TCA8418 provides 18 GPIO pins organized as:
- **Rows**: `gpio_rows[0]` through `gpio_rows[7]` (ROW0-ROW7)
- **Columns**: `gpio_cols[0]` through `gpio_cols[9]` (COL0-COL9)

These pins can be configured as:
- Matrix keypad scanner inputs/outputs
- General purpose digital I/O
- Interrupt sources

## I2C Configuration

The TCA8418 has a **fixed I2C address of 0x34** (7-bit addressing). Unlike some I2C devices, this address cannot be changed through hardware pins, which means only one TCA8418 can be used per I2C bus without additional hardware like I2C multiplexers.

## Interrupt Functionality

The device provides an interrupt output pin that is:
- **Active low** (pulls low when interrupt occurs)
- **Open drain** (requires external pull-up resistor)
- Configurable interrupt sources include key press/release events and GPIO state changes

## Power Supply

The module operates from **1.8V to 3.6V** and includes:
- Built-in decoupling capacitors (2x 100nF)
- Low standby current consumption (3μA)
- Compatible with both 3.3V and 1.8V logic levels

## Hardware Details

- **Package**: WQFN-24-EP (4x4mm)
- **Manufacturer**: Texas Instruments
- **Part Number**: TCA8418RTWR
- **LCSC Part Number**: C138713
- **Adafruit Product ID**: 4918

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
