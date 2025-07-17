# STMicroelectronics LPS22 Nano Pressure Sensor

The LPS22 is an ultra-compact MEMS nano pressure sensor featuring high accuracy and low power consumption. It delivers excellent pressure measurement accuracy and stability over temperature and time.

## Key Features

- **Pressure measurement**: 260-1260 hPa (±1 hPa accuracy)
- **High resolution**: 0.0075 hPa (0.065 cm altitude resolution)
- **Low power consumption**: 3 µA in one-shot mode, 12 µA at 75 Hz
- **Fast output data rate**: up to 200 Hz
- **Dual interface**: I²C and SPI communication
- **Wide supply voltage**: 1.7V to 3.6V
- **Small package**: LGA-10 (2.0mm × 2.0mm × 0.73mm)
- **Address selection**: 0x5C or 0x5D via SA0 pin
- **Temperature compensation**: Built-in temperature sensor

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "st-lps22.ato" import ST_LPS22

module Usage:
    """
    Minimal usage example for st-lps22.
    Demonstrates basic I²C connection with 3.3V power supply.
    The sensor will be configured at I2C address 0x5C (SA0 pin pulled low).
    """

    # Sensor instance
    sensor = new ST_LPS22

    # External I²C bus
    i2c = new I2C
    """External I2C bus for sensor communication"""
    i2c ~ sensor.i2c

    # Power supply (3.3V rail)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # Connect power supply
    power_3v3 ~ sensor.power

    # Provide I2C bus reference voltage
    power_3v3 ~ i2c.scl.reference
    power_3v3 ~ i2c.sda.reference

    # Configure I²C address to 0x5C (SA0 pin will be pulled low)
    sensor.i2c.address = 0x5C
```

## Interface Details

### I2C Communication
- **Addresses**: 0x5C (SA0=LOW) or 0x5D (SA0=HIGH)
- **Clock speeds**: Standard mode (100 kHz), Fast mode (400 kHz), Fast mode plus (1 MHz)
- **Data format**: 24-bit pressure and 16-bit temperature data

### SPI Communication
- **Clock speed**: Up to 10 MHz
- **Mode**: SPI mode 0 (CPOL=0, CPHA=0) and mode 3 (CPOL=1, CPHA=1)
- **Chip select**: Active low
- **Data format**: MSB first

### Power Supply
- **VDD**: 1.7V to 3.6V (typical 3.3V)
- **Current consumption**:
  - One-shot mode: 3 µA
  - Continuous mode (75 Hz): 12 µA
  - Power-down mode: 1 µA

### Address Selection
The I2C address is determined by the SA0 pin:
- **SA0 = LOW**: Address = 0x5C
- **SA0 = HIGH**: Address = 0x5D

### Interrupt Features
- Data ready interrupt
- Pressure threshold interrupts (high/low)
- FIFO watermark and overrun interrupts
- Open-drain, active low output

## Package Information
- **Package type**: LGA-10 (Land Grid Array)
- **Dimensions**: 2.0mm × 2.0mm × 0.73mm
- **Pin pitch**: 0.5mm
- **Operating temperature**: -40°C to +85°C

## Applications
- Wearable devices and fitness trackers
- Indoor navigation and floor detection
- Weather stations and environmental monitoring
- Industrial automation and HVAC systems
- Smartphone and tablet barometers
- GPS enhancement for outdoor applications

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
