# STMicroelectronics LPS28DFW Pressure Sensor

Ultra-compact piezoresistive absolute pressure sensor with dual full-scale ranges (1260 hPa and 4060 hPa) and water-resistant package. The LPS28DFW features I²C digital interface and operates from -40°C to +85°C.

## Features

- **Dual pressure range**: 1260 hPa and 4060 hPa full-scale
- **Wide operating temperature**: -40°C to +85°C
- **I²C digital interface** with configurable 7-bit address
- **Ultra-low power consumption**
- **Water-resistant package** with metal lid
- **High pressure capability**: up to 10,000 hPa with potting gel protection
- **Supply voltage**: 1.7V to 3.6V

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import I2C
import ElectricPower

from "atopile/st-lps28/st-lps28.ato" import ST_LPS28

module Usage:
    """
    Minimal usage example for ST LPS28 pressure sensor.
    Shows basic connections for pressure measurement with I2C interface.
    """

    # Create sensor instance
    pressure_sensor = new ST_LPS28

    # Create I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz  # Fast mode I2C

    # Create power supply (3.3V typical)
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.15V to 3.45V  # 3.3V ±5%

    # Connect interfaces
    i2c_bus ~ pressure_sensor.i2c
    power_3v3 ~ pressure_sensor.power

    # Set I2C address (SA0 connected to GND = 0x5C, SA0 connected to VDD = 0x5D)
    assert pressure_sensor.i2c.address is 0x5C

```

## Pin Configuration

- **VDD**: Power supply (1.7V to 3.6V)
- **GND**: Ground connection
- **SDA**: I²C data line
- **SCL**: I²C clock line
- **SA0**: Address selection pin (0x5C when low, 0x5D when high)
- **INT_DRDY**: Interrupt/Data ready output (optional)
- **PAD2LID**: Pressure pad to lid connection

## I²C Address Configuration

The device has a 7-bit I²C address that can be configured using the SA0 pin:
- SA0 = 0 (GND): Address = 0x5C
- SA0 = 1 (VDD): Address = 0x5D

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
