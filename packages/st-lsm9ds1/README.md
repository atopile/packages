# STMicroelectronics LSM9DS1 9-DOF IMU

The STMicroelectronics LSM9DS1 is a system-in-package featuring a 3D digital linear acceleration sensor, a 3D digital angular rate sensor, and a 3D digital magnetic sensor. It includes a sensing element and an IC interface which communicates through I2C/SPI serial interfaces.

## Features

- **3-axis linear accelerometer**: ±2/±4/±8/±16 g programmable full scale
- **3-axis angular rate sensor**: ±245/±500/±2000 dps programmable full scale
- **3-axis magnetic sensor**: ±4/±8/±12/±16 gauss programmable full scale
- **Dual communication interfaces**: I2C (mandatory) and SPI (optional)
- **Dual I2C addressing**: Separate addresses for accelerometer/gyroscope and magnetometer
- **Built-in pull-up resistors**: 4.7kΩ I2C pull-ups and 10kΩ chip select pull-ups
- **Interrupt pins**: Configurable interrupt outputs for both sensor units
- **Low power consumption**: Suitable for battery-powered applications

## I2C Address Configuration

The LSM9DS1 contains two functional units with separate I2C addresses:

| Unit | SDO Pin State | I2C Address | Notes |
|------|---------------|-------------|-------|
| Accelerometer/Gyroscope | SDO_A_G High | 0x6B | Default configuration |
| Accelerometer/Gyroscope | SDO_A_G Low | 0x6A | Alternative address |
| Magnetometer | SDO_M High | 0x1E | Default configuration |
| Magnetometer | SDO_M Low | 0x1C | Alternative address |

Both units share the same I2C bus but are accessed using different slave addresses.

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower
import I2C

from "atopile/st-lsm9ds1/st-lsm9ds1.ato" import ST_LSM9DS1

module Usage:
    """
    Minimal usage example for `st-lsm9ds1`.
    Shows how to connect the LSM9DS1 9-DOF IMU to power and I2C bus.

    This example demonstrates I2C mode with default addressing:
    - Accelerometer/Gyroscope: 0x6B (default when SDO_A_G is high)
    - Magnetometer: 0x1E (internal address when SDO_M is high)
    """

    imu = new ST_LSM9DS1

    # Power supplies
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # I2C bus (supports 100kHz-400kHz)
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz

    # Connections
    # Connect both power domains to same 3.3V supply (typical configuration)
    power_3v3 ~ imu.power_core    # VDD: sensor core power
    power_3v3 ~ imu.power_io      # VDDIO: I/O interface power
    i2c_bus ~ imu.i2c

    # I2C address will be 0x6B (default when SDO_A_G pulled high by internal resistor)
    # Magnetometer uses separate address 0x1E on the same I2C bus

```

## Pin Configuration

### Communication Interfaces

**I2C Mode (Default)**:
- Built-in 4.7kΩ pull-up resistors on SCL and SDA lines
- Built-in 10kΩ pull-up resistors on CS pins (enables I2C mode)
- Dual addressing for accelerometer/gyroscope and magnetometer units

**SPI Mode (Optional)**:
- Optional SPI interface available via `spi`, `spi_cs_ag`, and `spi_cs_m` connections
- SDO_A_G pin becomes MISO in SPI mode

### Interrupt Pins

- `int1_ag`: Interrupt 1 for accelerometer/gyroscope
- `int2_ag`: Interrupt 2 for accelerometer/gyroscope
- `int_m`: Interrupt for magnetometer
- `drdy_m`: Data ready signal for magnetometer

## Power Supply

The LSM9DS1 has separate power domains that can be independently controlled:

- **power_core (VDD)**: 2.16V to 3.6V (sensor core power)
- **power_io (VDDIO)**: 1.71V to 3.6V (I/O interface power)
- **Typical operating voltage**: 3.3V for both domains
- **Temperature range**: -40°C to +85°C

### Power Supply Configurations

**Same voltage (typical)**:
```ato
power_3v3 ~ imu.power_core
power_3v3 ~ imu.power_io
```

**Level shifting (1.8V I/O with 3.3V core)**:
```ato
power_3v3 ~ imu.power_core    # 3.3V sensor core
power_1v8 ~ imu.power_io      # 1.8V I/O interface
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
