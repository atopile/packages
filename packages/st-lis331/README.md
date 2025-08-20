# STMicroelectronics LIS331DLH Triple-Axis Digital Accelerometer

The LIS331DLH is a high-performance triple-axis digital accelerometer with selectable measurement ranges of ±2g, ±4g, and ±8g. It features 16-bit resolution, configurable data rates, and both I2C and SPI interfaces. The device includes programmable interrupt generators, embedded self-test capabilities, and advanced power management features.

## Features

- **Measurement Ranges**: ±2g, ±4g, ±8g on three axes
- **Resolution**: 16-bit data output
- **Interfaces**: I2C and SPI digital output
- **Power Supply**: 2.16V to 3.6V (VDD), 1.71V to VDD (VDD_IO)
- **I2C Address**: 0x19 (default with internal pull-up) or 0x18 (SDO/SA0 tied to GND)
- **Interrupts**: 2 programmable interrupt generators
- **Additional Features**: Configurable filters, sleep mode, self-test

## Usage

```ato
import I2C
import ElectricPower

from "atopile/st-lis331/st-lis331.ato" import ST_LIS331

module Usage:
    """
    Minimal usage example for ST_LIS331.
    Demonstrates basic connections for I2C communication with the accelerometer.
    """

    accelerometer = new ST_LIS331

    # Power supplies
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    power_io = new ElectricPower
    power_io.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.address = 0x19  # Default address (SDO/SA0 = 1 with internal pull-up)
    i2c_bus.frequency = 400kHz

    # Connect power
    power_3v3 ~ accelerometer.power
    power_io ~ accelerometer.power_io

    # Connect I2C
    i2c_bus ~ accelerometer.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
