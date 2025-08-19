# MEMSIC MMC5603 3-Axis Magnetometer

The MMC5603 is a 3-axis anisotropic magnetoresistive (AMR) magnetic sensor from MEMSIC. This ultra-small sensor provides high-precision magnetic field measurements with excellent temperature stability and low noise performance.

## Features

- **3-axis magnetic field sensing** with ±30G full-scale range
- **Ultra-small package**: 0.8mm x 0.8mm x 0.4mm wafer-level package
- **Wide operating voltage**: 1.62V to 3.6V (typical 1.8V)
- **I2C interface** with 7-bit address 0x30
- **High resolution**: Up to 0.0625mG per LSB at 20-bit operation mode
- **Low noise**: 2mG total RMS noise level
- **Wide temperature range**: -40°C to +85°C
- **Integrated SET/RESET function** eliminates temperature drift and residual magnetization

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import I2C

from "atopile/memsic-mmc5603/memsic-mmc5603.ato" import MEMSIC_MMC5603

module Usage:
    """
    Minimal usage example for MEMSIC MMC5603 magnetometer.
    Shows how to connect power supply and I2C bus to the sensor.
    """

    # Create sensor instance
    magnetometer = new MEMSIC_MMC5603

    # External power supply (1.8V typical)
    power_1v8 = new ElectricPower
    power_1v8.voltage = 1.8V +/- 5%

    # External I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect interfaces
    power_1v8 ~ magnetometer.power
    i2c_bus ~ magnetometer.i2c

```

## Technical Specifications

- **Supply Voltage**: 1.62V to 3.6V (typical 1.8V)
- **I2C Address**: 0x30 (7-bit)
- **Full-Scale Range**: ±30G
- **Resolution**: Up to 0.0625mG per LSB (20-bit mode)
- **Noise**: 2mG total RMS
- **Temperature Range**: -40°C to +85°C
- **Package**: WLP-4 (0.8mm x 0.8mm x 0.4mm)

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| A1  | VSA  | Ground/Analog Supply |
| A2  | SCL  | I2C Serial Clock |
| B1  | VDD  | Power Supply |
| B2  | SDA  | I2C Serial Data |

## Applications

- Electronic compass and navigation systems
- Drone and UAV orientation sensing
- Industrial automation and robotics
- Automotive applications
- Consumer electronics positioning
- Magnetic field detection and monitoring

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
