# Bosch BMP280 Temperature & Pressure Sensor

The BMP280 is a digital temperature and pressure sensor featuring high accuracy and low power consumption. It is based on Bosch's proven piezo-resistive pressure sensor technology with an accuracy down to 0.12 hPa, ultra-low power consumption, and a robust design.

## Key Features

- **Pressure measurement**: 300-1100 hPa (±1 hPa accuracy)
- **Temperature measurement**: -40°C to +85°C (±1°C accuracy)
- **Low power consumption**: 2.7 µA @ 1 Hz sampling
- **High resolution**: Up to 0.16 Pa (13 cm) altitude resolution
- **Dual interface**: I²C and SPI communication
- **Wide supply voltage**: 1.71V to 3.6V (VDD), 1.2V to 3.6V (VDDIO)
- **Small package**: LGA-8 (2.0mm × 2.5mm × 0.95mm)
- **Address selection**: 0x76 or 0x77 via SDO pin

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/bosch-bmp280/bosch-bmp280.ato" import Bosch_BMP280

module Usage:
    """
    Minimal usage example for bosch-bmp280.
    Demonstrates basic I²C connection with 3.3V power supply.
    The sensor will be configured at I2C address 0x76 (SDO pin pulled low).
    """

    # Sensor instance
    sensor = new Bosch_BMP280

    # External I²C bus
    i2c = new I2C
    """External I2C bus for sensor communication"""
    i2c ~ sensor.i2c

    # Power supply (3.3V rail for both core and I/O)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Connect both power rails to the same 3.3V supply
    power_3v3 ~ sensor.power_core
    power_3v3 ~ sensor.power_io

    # Provide I2C bus reference voltage
    power_3v3 ~ i2c.scl.reference
    power_3v3 ~ i2c.sda.reference

    # Configure I²C address to 0x76 (SDO pin will be pulled low via internal pull-down)
    sensor.i2c.address = 0x76

```

## Interface Details

### I2C Communication
- **Addresses**: 0x76 (SDO=LOW) or 0x77 (SDO=HIGH)
- **Clock speeds**: Standard mode (100 kHz), Fast mode (400 kHz)
- **Data format**: 16-bit and 20-bit measurement data

### SPI Communication
- **Clock speed**: Up to 10 MHz
- **Modes**: 3-wire and 4-wire SPI
- **Chip select**: Active low

### Power Supply
- **VDD (Core)**: 1.71V to 3.6V (typical 3.3V)
- **VDDIO (I/O)**: 1.2V to 3.6V (can be same as VDD)
- **Current consumption**:
  - Normal mode: 714 µA (pressure + temperature)
  - Sleep mode: 0.1 µA

### Address Selection
The I2C address is determined by the SDO pin:
- **SDO = LOW**: Address = 0x76
- **SDO = HIGH**: Address = 0x77

## Package Information
- **Package type**: LGA-8 (Land Grid Array)
- **Dimensions**: 2.0mm × 2.5mm × 0.95mm
- **Pin pitch**: 0.65mm
- **Recommended PCB land pattern**: Included in footprint

## Applications
- Indoor navigation
- Health care applications (e.g., spirometry)
- Weather forecast
- Vertical velocity indication (climb/sink speed)
- Sports applications
- GPS enhancement (dead-reckoning)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
