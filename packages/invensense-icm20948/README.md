# InvenSense ICM-20948 9-Axis Motion Sensor

The InvenSense ICM-20948 is a comprehensive 9-axis motion tracking device featuring a 3-axis gyroscope, 3-axis accelerometer, and 3-axis magnetometer (compass) with an integrated Digital Motion Processor (DMP). This sensor is ideal for advanced motion tracking applications requiring high precision and low power consumption.

## Key Features

- **3-Axis Gyroscope**: ±250, ±500, ±1000, ±2000 dps full scale ranges
- **3-Axis Accelerometer**: ±2g, ±4g, ±8g, ±16g full scale ranges
- **3-Axis Magnetometer**: ±4900 µT full scale range (AK09916)
- **Digital Motion Processor (DMP)**: On-chip sensor fusion and motion processing
- **Dual Power Supplies**: VDD (1.71V-3.6V) and VDDIO (1.71V-1.95V)
- **Communication Interfaces**: I²C (up to 400kHz) and SPI (up to 7MHz)
- **Configurable I²C Address**: 0x68 or 0x69 via SDO/AD0 pin
- **Programmable Interrupts**: Motion detection and data ready
- **Auxiliary I²C Master**: Interface for external sensors
- **Built-in Temperature Sensor**: Integrated temperature measurement
- **Low Power Modes**: Multiple power management options
- **Package**: 24-pin QFN (3mm x 3mm x 1mm)

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")
#pragma experiment("FOR_LOOP")

import I2C
import ElectricPower
import ElectricLogic

from "invensense-icm20948.ato" import ICM20948

module Usage:
    """
    Usage example for the InvenSense ICM-20948 9-axis motion sensor.
    Demonstrates basic I²C connections with dual power supplies.
    """

    # --- IMU sensor ---
    imu = new ICM20948

    # --- Power supplies ---
    power_3v3 = new ElectricPower  # Core power (VDD)
    assert power_3v3.voltage within 3.2V to 3.4V

    power_1v8 = new ElectricPower  # I/O power (VDDIO)
    assert power_1v8.voltage within 1.7V to 1.9V

    # --- I²C bus ---
    i2c_bus = new I2C
    assert i2c_bus.frequency <= 400kHz
    # I2C address is automatically configured by the sensor (0x68 by default)

    # --- Optional control signals ---
    interrupt_pin = new ElectricLogic
    frame_sync = new ElectricLogic

    # --- Connections ---
    power_3v3 ~ imu.power_core
    power_1v8 ~ imu.power_io
    i2c_bus ~ imu.i2c
    interrupt_pin ~ imu.interrupt
    frame_sync ~ imu.fsync
```

## Interfaces

### Required
- **power_core**: ElectricPower interface (VDD: 1.71V to 3.6V)
- **power_io**: ElectricPower interface (VDDIO: 1.71V to 1.95V)
- **i2c**: I²C interface for communication

### Optional
- **spi**: SPI interface (alternative to I²C, up to 7MHz)
- **cs**: SPI Chip Select pin (active low)
- **interrupt**: Interrupt pin (INT1) - programmable output
- **fsync**: Frame synchronization input pin
- **aux_i2c**: Auxiliary I²C interface for external sensors
- **regulator_output**: 1.8V regulator output (up to 50mA)

## Power Configuration

The ICM-20948 requires dual power supplies:

- **VDD (Core Power)**: 1.71V to 3.6V (typical: 3.3V)
- **VDDIO (I/O Power)**: 1.71V to 1.95V (typical: 1.8V)
- **Current Consumption**:
  - Active mode: ~3.4mA (all sensors enabled)
  - Low power mode: ~68.9µA (accelerometer only)
  - Sleep mode: ~8.5µA

## I²C Address Configuration

The I²C address is determined by the SDO/AD0 pin:

| SDO/AD0 Connection | I²C Address |
|-------------------|-------------|
| GND (Default) | 0x68 |
| VDD | 0x69 |

## Pin Configuration

- **VDD**: Core power supply (1.71V-3.6V)
- **VDDIO**: I/O voltage reference (1.71V-1.95V)
- **GND**: Ground
- **SCL/SCLK**: I²C clock / SPI clock
- **SDA/SDI**: I²C data / SPI data input
- **SDO/AD0**: SPI data output / I²C address select
- **nCS**: SPI chip select (active low)
- **INT1**: Interrupt output
- **FSYNC**: Frame synchronization input
- **AUX_CL**: Auxiliary I²C clock
- **AUX_DA**: Auxiliary I²C data
- **REGOUT**: 1.8V regulator output

## Applications

- Drones and UAVs
- Virtual/Augmented Reality systems
- Gaming controllers
- Motion capture systems
- Robotics navigation
- Fitness trackers
- Smartphone orientation sensing
- Industrial motion monitoring

## Technical Specifications

- **Supply Voltage**: VDD 1.71V-3.6V, VDDIO 1.71V-1.95V
- **Communication**: I²C (400kHz max) or SPI (7MHz max)
- **Gyroscope Range**: ±250, ±500, ±1000, ±2000 dps
- **Accelerometer Range**: ±2g, ±4g, ±8g, ±16g
- **Magnetometer Range**: ±4900 µT
- **Operating Temperature**: -40°C to +85°C
- **Package**: 24-pin QFN (3mm x 3mm x 1mm)

## Package Information

- **Manufacturer**: TDK InvenSense
- **Part Number**: ICM-20948
- **LCSC Part**: C726001
- **Package**: QFN-24 (3mm x 3mm)

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
