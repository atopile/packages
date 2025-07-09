# Analog Devices ADXL375

The ADXL375 is a small, thin, 3-axis accelerometer that provides
low power consumption and high resolution measurement up
to ±200 g. The digital output data is formatted as 16-bit, with I²C digital interface.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/adi-adxl375/adi-adxl375.ato" import ADI_ADXL375

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the ADI_ADXL375 accelerometer."""

    # MCU & sensor
    mcu = new MCU
    accelerometer = new ADI_ADXL375

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ accelerometer.power

    # I²C connection
    mcu.i2c ~ accelerometer.i2c
    accelerometer.i2c.address = 0x53
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
