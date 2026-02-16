# STMicroelectronics STUSB4500 USB PD Controller

USB Power Delivery controller supporting up to 20V/5A with an I²C interface for configuration and status. This package provides a ready-to-use driver and a Type‑C connector wrapper with USB2 pass‑through and CC handling.

## Usage

```ato
import ElectricPower
import USB2_0
import I2C

from "atopile/st-stusb4500/st-stusb4500.ato" import STUSB4500_USBC_Connector

module Usage:
    stusb4500 = new STUSB4500_USBC_Connector
    usb2 = new USB2_0

    power = new ElectricPower
    power ~ stusb4500.driver.power_vsink

    usb2 ~ stusb4500.driver.usb2

    i2c = new I2C
    stusb4500.driver.i2c ~ i2c
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
