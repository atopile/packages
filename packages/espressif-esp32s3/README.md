# Espressif ESP32-S3-WROOM-1/1U Module

This package provides the module definition for the ESP32-S3-WROOM-1 and ESP32-S3-WROOM-1U.

## Usage

```ato
import ElectricPower
import Espressif_ESP32S3 from "espressif-esp32s3.ato"
# Assuming installed packages via registry or local paths
from "atopile/usb-connectors/usb-connectors.ato" import USBCConn
from "atopile/ti-tlv75901/ti-tlv75901.ato" import TLV75901_driver

module Usage:
    """
    Example usage of ESP32-S3
    """
    mcu = new Espressif_ESP32S3

    # Power Supply
    usb = new USBCConn
    ldo = new TLV75901_driver

    power_usb = new ElectricPower
    power_3v3 = new ElectricPower

    # USB Power -> LDO -> 3.3V
    usb.power ~ power_usb
    power_usb ~> ldo ~> power_3v3

    # Connect MCU Power
    mcu.power ~ power_3v3

    # Connect USB Data
    usb.usb2.dp ~ mcu.usb.dp
    usb.usb2.dm ~ mcu.usb.dm

    # Configure LDO
    ldo.v_out = 3.3V
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
