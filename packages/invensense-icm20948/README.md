# TDK InvenSense ICM-20948 9-DoF IMU

A comprehensive 9-axis motion tracking device featuring a 3-axis gyroscope, 3-axis accelerometer, and 3-axis compass with an onboard Digital Motion Processor (DMP).

## Features

- **3-axis gyroscope**: ±250, ±500, ±1000, ±2000 dps ranges
- **3-axis accelerometer**: ±2g, ±4g, ±8g, ±16g ranges
- **3-axis magnetometer**: ±4900 μT range
- **Digital Motion Processor (DMP)** for sensor fusion
- **Dual power supplies**: VDD (1.71V-3.6V) and VDDIO (1.71V-1.95V)
- **Communication interfaces**: I2C (400 kHz) and SPI (7 MHz)
- **Configurable I2C address**: 0x68 or 0x69 via AD0 pin
- **Interrupt output** for motion detection
- **Auxiliary I2C** for external sensor expansion

## Usage

```ato
from "atopile/invensense-icm20948/icm20948.ato" import ICM20948_driver

module MyProject:
    # Power supplies
    power_3v3 = new ElectricPower
    power_1v8 = new ElectricPower

    # IMU sensor
    imu = new ICM20948_driver

    # I2C bus
    i2c_bus = new I2C

    # Connections
    power_3v3 ~ imu.power_vdd
    power_1v8 ~ imu.power_vddio
    i2c_bus ~ imu.i2c
```

## Power Requirements

- **VDD**: 1.71V to 3.6V (main power supply)
- **VDDIO**: 1.71V to 1.95V (I/O voltage reference)
- **Current consumption**: ~2.5mW typical

## I2C Address Configuration

The I2C address is configurable via the AD0 pin:
- AD0 = LOW: Address 0x68
- AD0 = HIGH: Address 0x69

The driver uses an `Addressor` module to handle this configuration automatically.

## Package Information

- **Manufacturer**: TDK InvenSense
- **Part Number**: ICM-20948
- **JLCPCB Part**: C726001
- **Package**: QFN-24 (3x3mm)

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
