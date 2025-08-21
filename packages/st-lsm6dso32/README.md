# STMicroelectronics LSM6DSO32 6-DoF Accelerometer and Gyroscope

High-performance 6-axis inertial measurement unit (IMU) with 3-axis accelerometer and 3-axis gyroscope. Features extended accelerometer range up to ±32g and advanced motion sensing capabilities.

## Features

- **3-axis accelerometer**: ±4/±8/±16/±32g selectable ranges
- **3-axis gyroscope**: ±125/±250/±500/±1000/±2000 dps selectable ranges
- **High output data rates**: 1.6 Hz to 6.7 kHz (accelerometer), 12.5 Hz to 6.7 kHz (gyroscope)
- **Advanced motion detection**: Built-in tap detection, activity detection, pedometer/step counter
- **Dual communication interfaces**: I2C and SPI support
- **Configurable interrupts**: Two programmable interrupt pins
- **Low power consumption**: Multiple power modes for optimized battery life
- **Programmable FSM**: Finite state machine for basic gesture recognition

## Usage

### Basic I2C Configuration

```ato
#pragma experiment("TRAITS")
import ElectricPower
import I2C
import ElectricLogic
from "atopile/st-lsm6dso32/st-lsm6dso32.ato" import ST_LSM6DSO32

module Usage:
    """
    Usage example for ST LSM6DSO32 6-DoF Accelerometer and Gyroscope.

    This example shows:
    - Single power supply configuration (VDD and VDDIO connected to same rail)
    - I2C interface with default address 0x6A
    - Address selection via SA0 pin (connected to GND for 0x6A)
    - Optional interrupt pin connection
    """

    # Power supply (3.3V single rail for both VDD and VDDIO)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz +/- 50%

    # IMU sensor
    imu = new ST_LSM6DSO32

    # Connect power supplies (single supply configuration)
    power_3v3 ~ imu.power_vdd
    power_3v3 ~ imu.power_vddio

    # Connect I2C interface
    i2c_bus ~ imu.i2c

    # Configure I2C address to 0x6A (SA0 pin to GND)
    i2c_bus.address = 0x6A

    # Connect SA0 pin to GND for 0x6A address
    # For 0x6B address, connect to VDD instead
    ground_ref = new ElectricLogic
    ground_ref.reference ~ power_3v3
    ground_ref.line ~ power_3v3.lv  # Connect to ground
    ground_ref ~ imu.sdo_sa0

    # Optional: Connect interrupt pin for motion detection
    # int_pin = new ElectricLogic
    # int_pin.reference ~ power_3v3
    # int_pin ~ imu.int1

```

### Advanced Configurations

#### Dual Power Supply Configuration
```ato
# Separate power supplies for optimized performance
power_1v8 = new ElectricPower  # Core supply
power_1v8.voltage = 1.8V +/- 5%

power_3v3 = new ElectricPower  # I/O supply
power_3v3.voltage = 3.3V +/- 5%

imu = new ST_LSM6DSO32
power_1v8 ~ imu.power_vdd     # Core at 1.8V
power_3v3 ~ imu.power_vddio   # I/O at 3.3V
```

#### Alternative I2C Address (0x6B)
```ato
# Connect SA0 to VDD for 0x6B address
vdd_ref = new ElectricLogic
vdd_ref.reference ~ power_3v3
vdd_ref.line ~ power_3v3.hv  # Connect to VDD
vdd_ref ~ imu.sdo_sa0
i2c_bus.address = 0x6B
```

#### SPI Configuration (Optional)
```ato
# Note: SPI and I2C are mutually exclusive
# When using SPI, connect sdo_sa0 to microcontroller MISO
# and actively control the cs pin
spi_bus = new SPI
spi_bus ~ imu.spi
imu.sdo_sa0 ~ spi_bus.miso  # Connect to SPI MISO
imu.cs ~ spi_cs_pin         # Connect to SPI chip select
```

## Technical Specifications

- **Supply voltage**: 1.71V to 3.6V (VDD), 1.62V to 3.6V (VDDIO)
- **I2C addresses**: 0x6A (SA0 to GND) or 0x6B (SA0 to VDD)
- **I2C pull-up resistors**: 4.7kΩ ±5% (built-in, optimized for up to 400kHz)
- **SPI interface**: Up to 10 MHz
- **Temperature range**: -40°C to +85°C
- **Package**: LGA-14 (2.5mm × 3.0mm)

## Built-in Components

- **CS pull-up**: 10kΩ ±10% (ensures I2C mode operation)
- **I2C pull-ups**: 4.7kΩ ±5% on SCL and SDA lines
- **Decoupling capacitors**: 100nF ±20% on both VDD and VDDIO rails

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
