# STMicroelectronics LSM6DSOX + LIS3MDL 9-DoF IMU

This package provides a driver for the STMicroelectronics LSM6DSOX + LIS3MDL 9-DoF IMU combo sensor, based on the Adafruit breakout board (Product ID: 4517).

The sensor combines:
- **LSM6DSOX**: 6-axis IMU with 3-axis accelerometer and 3-axis gyroscope
- **LIS3MDL**: 3-axis magnetometer

## Features

- **9 degrees of freedom**: 3-axis accelerometer, 3-axis gyroscope, 3-axis magnetometer
- **Dual I²C interfaces** with configurable addresses:
  - LSM6DSOX: 0x6A or 0x6B (configurable via SA0)
  - LIS3MDL: 0x1C or 0x1E (configurable via SA1)
- **Wide power supply range**: 3V-5V with onboard voltage regulation
- **STEMMA QT / Qwiic connectors** for easy daisy-chaining
- **Multiple interrupt pins** available:
  - LSM6DSOX: INT1, INT2 (programmable)
  - LIS3MDL: INT, DRDY (interrupt and data ready)
- **Machine learning core** support (LSM6DSOX)
- **Auxiliary sensor interface** (LSM6DSOX can read LIS3MDL data directly)

## Specifications

### LSM6DSOX (6-axis IMU)
- **Accelerometer ranges**: ±2/±4/±8/±16 g
- **Gyroscope ranges**: ±125/±250/±500/±1000/±2000 dps
- **Update rates**: 1.6 Hz to 6.7 kHz
- **Machine learning core** with finite state machine
- **Power supply**: VDD = 1.71V-3.6V, VDDIO = 1.62V-3.6V
- **I2C addresses**: 0x6A (SA0=LOW) or 0x6B (SA0=HIGH)

### LIS3MDL (3-axis Magnetometer)
- **Magnetic field ranges**: ±4/±8/±12/±16 gauss
- **Update rates**: 0.625 Hz to 1 kHz
- **High resolution**: 16-bit data output
- **Power supply**: VDD = 2.16V-3.6V, VDDIO = 1.71V-3.6V
- **I2C addresses**: 0x1C (SA1=LOW) or 0x1E (SA1=HIGH)

### Combined System
- **Effective power range**: 2.16V-3.6V (to meet both sensor requirements)
- **Total degrees of freedom**: 9 (3 accelerometer + 3 gyroscope + 3 magnetometer)
- **I2C frequency**: Up to 400 kHz

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/st-lsm6dsox-lis3mdl/st-lsm6dsox-lis3mdl.ato" import ST_LSM6DSOX_LIS3MDL

module Usage:
    """
    Comprehensive usage example for ST_LSM6DSOX_LIS3MDL.
    Shows how to connect power and I2C to the 9-DoF IMU combo sensor.

    This example demonstrates:
    - Power supply connection (3V-5V)
    - I2C bus connection shared by both sensors
    - Optional interrupt pin connections

    I2C Addresses:
    - LSM6DSOX (6-axis IMU): 0x6A or 0x6B
    - LIS3MDL (magnetometer): 0x1C or 0x1E
    """

    imu_combo = new ST_LSM6DSOX_LIS3MDL

    # Power supply (3V-5V)
    power_supply = new ElectricPower
    power_supply.voltage = 3.3V +/- 5%
    power_supply ~ imu_combo.power

    # I2C bus (shared by both LSM6DSOX and LIS3MDL)
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz
    i2c_bus ~ imu_combo.i2c

    # Optional: Connect interrupt pins if needed
    # LSM6DSOX interrupt pins
    # imu_combo.imu_int1 can be connected to a microcontroller GPIO
    # imu_combo.imu_int2 can be connected to a microcontroller GPIO

    # LIS3MDL interrupt pins
    # imu_combo.mag_int can be connected to a microcontroller GPIO
    # imu_combo.mag_drdy can be connected to a microcontroller GPIO

    # Note: Both sensors will be accessible on the same I2C bus:
    # - Read accelerometer/gyroscope data from LSM6DSOX at 0x6A/0x6B
    # - Read magnetometer data from LIS3MDL at 0x1C/0x1E
    # - LSM6DSOX can also read LIS3MDL data through its auxiliary interface

```

## Pinout

The module exposes the following interfaces:

### Power Supply
- `power`: Main power supply (3V-5V)

### Communication
- `i2c`: I²C bus interface (shared by both sensors)

### LSM6DSOX Interrupt Pins
- `imu_int1`: Interrupt 1 pin (LSM6DSOX)
- `imu_int2`: Interrupt 2 pin (LSM6DSOX)

### LIS3MDL Interrupt Pins
- `mag_int`: Interrupt pin (LIS3MDL)
- `mag_drdy`: Data ready pin (LIS3MDL)

## I2C Addresses

- **LSM6DSOX**: 0x6A (default) or 0x6B (configurable via SA0 pin)
- **LIS3MDL**: 0x1C (default) or 0x1E (configurable via SA1 pin)

## Advanced Features

- **Auxiliary Sensor Interface**: The LSM6DSOX can read LIS3MDL data through its auxiliary sensor interface, allowing synchronized reading of all 9 axes
- **Machine Learning Core**: LSM6DSOX includes a machine learning core for advanced motion detection
- **Dual Power Rails**: Separate VDD and VDDIO power rails for optimal power management

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
