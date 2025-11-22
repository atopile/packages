# Espressif ESP32-S3-WROOM-1/1U Module

This package provides the module definition for the ESP32-S3-WROOM-1 and ESP32-S3-WROOM-1U.

## Features

*   **Power**: Integrated decoupling capacitors for 3.3V rail.
*   **Control**: Enable/Reset pin with RC delay circuit and pull-up.
*   **Buttons**: Integrated Boot (IO0) and Reset (Enable) buttons (vertical).
*   **Interfaces**:
    *   `uart0`: UART interface (TX/RX).
    *   `usb`: Native USB 2.0 interface (D+/D-).
    *   `i2c`: I2C interface (Default: SDA=IO8, SCL=IO9).
    *   `spi`: SPI interface (Default: MOSI=IO11, MISO=IO13, SCK=IO12).
    *   `touch`: Array of 14 capacitive touch pins (TOUCH1-TOUCH14).
    *   `io`: Array of all accessible GPIO pins (ElectricLogic).

## Usage

```ato
import ElectricPower
import USB2_0
import Espressif_ESP32S3 from "espressif-esp32s3/espressif-esp32s3.ato"

# Mock modules for usage example
module USBCConn:
    power = new ElectricPower
    usb = new USB2_0

module LDO:
    power_in = new ElectricPower
    power_out = new ElectricPower
    v_out = 3.3V

module Usage:
    """
    Example usage of ESP32-S3
    """
    mcu = new Espressif_ESP32S3

    # Components
    usb = new USBCConn
    ldo = new LDO

    # Connections
    usb.power ~ ldo.power_in
    ldo.power_out ~ mcu.power

    # USB Data
    usb.usb.usb_if.d.p ~ mcu.usb.usb_if.d.p
    usb.usb.usb_if.d.n ~ mcu.usb.usb_if.d.n

    # LDO Config
    ldo.v_out = 3.3V
```

## Pin Mapping

*   **UART0**: TX (IO43), RX (IO44)
*   **USB**: D+ (IO20), D- (IO19)
*   **I2C**: SDA (IO8), SCL (IO9)
*   **SPI**: MOSI (IO11), MISO (IO13), SCK (IO12), CS (IO10)
*   **Touch**: Mapped to IO1-IO14

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
