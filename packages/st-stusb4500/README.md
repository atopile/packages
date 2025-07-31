# STMicroelectronics STUSB4500 USB PD Controller

The STUSB4500 is a USB Power Delivery (PD) controller that enables negotiation of up to 100W (20V/5A) from USB Type-C power sources. It provides an I2C interface for configuration and defaults to requesting 20V at 1A.

## Features

- USB PD 3.0 compliant sink controller
- Supports up to 20V/5A (100W) power delivery
- I2C interface for dynamic configuration
- USB 2.0 pass-through capability
- Configurable I2C address via ADDR0/ADDR1 pins
- Integrated CC (Configuration Channel) logic

## I2C Addressing

The 7-bit I2C address is determined by the ADDR0 and ADDR1 pins:

| ADDR1 | ADDR0 | 7-bit Address |
|-------|-------|---------------|
| 0     | 0     | 0x28          | (Default)
| 0     | 1     | 0x29          |
| 1     | 0     | 0x2A          |
| 1     | 1     | 0x2B          |

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C
import Resistor
import ElectricLogic

from "atopile/st-stusb4500/st-stusb4500.ato" import STUSB4500

module USBPDExample:
    """
    Example usage of STUSB4500 USB PD controller
    This example shows how to integrate the STUSB4500 to provide
    USB PD power to your project.
    """

    # Interfaces
    power_5v_to_20v = new ElectricPower  # Variable voltage from USB PD
    power_3v3 = new ElectricPower        # 3.3V for MCU
    i2c = new I2C                        # MCU I2C bus

    # USB PD controller
    usb_pd = new STUSB4500

    # Connect power output
    usb_pd.power_out ~ power_5v_to_20v

    # Connect MCU power (3.3V)
    usb_pd.power_mcu ~ power_3v3

    # Connect I2C for configuration
    usb_pd.i2c ~ i2c

    # Example: LED indicator for power good
    power_led = new ElectricLogic
    power_led.reference ~ power_3v3

    # Pull-up resistor for LED (active low)
    led_pullup = new Resistor
    led_pullup.resistance = 10kohm +/- 10%
    led_pullup.package = "0402"
    power_3v3.hv ~> led_pullup ~> power_led.line

    # Connect to PD controller power good signal
    power_led.line ~ usb_pd.pd_controller.pd_controller.POWER_OK2

    # Set I2C address (default is 0x28)
    assert i2c.address is 0x28
```

## Interfaces

- `power_out`: ElectricPower - Negotiated USB PD power output (5V-20V)
- `power_mcu`: ElectricPower - 3.3V power supply for the MCU interface
- `i2c`: I2C - Configuration interface
- `usb2`: USB2_0 - USB 2.0 pass-through for downstream devices

## Notes

- The module includes a USB Type-C connector (XKB Connectivity U262-241N-4BV64)
- Default power negotiation is 20V at 1A without I2C configuration
- The I2C interface allows dynamic power profile configuration
- USB 2.0 signals can be passed through to downstream devices

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
