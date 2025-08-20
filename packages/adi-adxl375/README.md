# ADI ADXL375 High-G 3-Axis Digital Accelerometer

The ADXL375 is a small, thin, ultralow power, 3-axis MEMS accelerometer with high resolution (13-bit) measurement at up to ±200 g. Digital output data is formatted as 16-bit twos complement and is accessible through either a SPI (3- or 4-wire) or I2C digital interface.

## Key Features

- **High measurement range**: ±200 g
- **High resolution**: 13-bit measurement resolution
- **Dual interfaces**: SPI (3/4-wire) and I2C
- **Low power**: 35 µA in measurement mode, 0.1 µA in standby
- **Wide supply voltage**: 2.0V to 3.6V
- **Small package**: 3mm × 5mm × 1mm LGA-14
- **High shock survival**: 10,000 g
- **Temperature range**: -40°C to +85°C

## Usage

```ato
import ElectricPower
import I2C

from "atopile/adi-adxl375/adi-adxl375.ato" import ADI_ADXL375

module Usage:
    """Minimal example for the ADI_ADXL375 accelerometer."""

    # Sensor instance
    accelerometer = new ADI_ADXL375

    # Power rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ accelerometer.power

    # I²C bus
    i2c = new I2C
    i2c ~ accelerometer.i2c
    accelerometer.i2c.address = 0x53

```

## Interface Options

### SPI Mode
- Set CS pin LOW for SPI operation
- Supports both 3-wire and 4-wire SPI
- Uses SCLK, MOSI, MISO pins

### I2C Mode
- Set CS pin HIGH for I2C operation
- 7-bit addressing: 0x53 (ALT=LOW) or 0x1D (ALT=HIGH)
- Standard and fast mode support (up to 400kHz)
- Requires external pull-up resistors on SCL/SDA

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
