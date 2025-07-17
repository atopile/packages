# STMicroelectronics LIS3DH 3-Axis MEMS Accelerometer

Ultra-low-power 3-axis MEMS accelerometer with embedded intelligence and digital output for consumer and industrial applications.

## Features

- **3-Axis Sensing**: X, Y, Z axis acceleration measurement
- **Wide Dynamic Range**: ±2g/±4g/±8g/±16g user selectable full-scale
- **Low Power**: Multiple power modes down to 2μA in low-power mode
- **Embedded Intelligence**: Motion detection, free-fall detection, 6D/4D orientation
- **Dual Interface**: I²C and SPI digital output interfaces
- **Auxiliary ADC**: 3 auxiliary analog-to-digital converters
- **Dual Interrupts**: Two programmable interrupt generators
- **Wide Supply Range**: 1.71V to 3.6V supply voltage

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C
import ElectricLogic

from "st-lis3dh.ato" import ST_LIS3DH

module Usage:
    """
    Minimal usage example for st-lis3dh.

    This example demonstrates basic I²C connection and interrupt usage
    for the LIS3DH 3-axis accelerometer.
    """

    sensor = new ST_LIS3DH

    # Connect external I²C bus
    i2c = new I2C
    i2c ~ sensor.i2c

    # Connect power supplies (can be the same rail)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    power_3v3 ~ sensor.power_core
    power_3v3 ~ sensor.power_io

    # Connect interrupt pins to microcontroller GPIOs
    interrupt1_gpio = new ElectricLogic
    interrupt2_gpio = new ElectricLogic

    interrupt1_gpio ~ sensor.interrupt1
    interrupt2_gpio ~ sensor.interrupt2

    # Set I²C address to 0x18 (SA0 pulled low)
    assert sensor.i2c.address is 0x18
```

## Applications

- **Motion Sensing**: Detect device orientation and movement
- **Gaming**: Gesture recognition and motion control
- **Display Orientation**: Automatic screen rotation
- **Activity Monitoring**: Step counting and activity tracking
- **Impact Detection**: Drop detection and shock monitoring
- **Free-Fall Detection**: Safety applications and data protection
- **Vibration Monitoring**: Industrial machinery monitoring

## Interface Options

### I²C Interface
- **Clock Speed**: Up to 400kHz (Fast Mode)
- **Address**: 0x18 (SA0=0) or 0x19 (SA0=1)
- **Pull-ups**: Internal pull-ups available or external required

### SPI Interface
- **Speed**: Up to 10MHz
- **Mode**: Mode 0 or Mode 3
- **CS**: Active low chip select

## Interrupt Features

- **INT1 & INT2**: Two independent interrupt pins
- **Configurable Events**: Motion, free-fall, orientation, click detection
- **Latching**: Interrupt latching and status reading
- **Activity/Inactivity**: Programmable thresholds and time windows

## Package Information

- **JLCPCB Part Number**: C15134
- **Package**: LGA-16 (3mm × 3mm, 0.5mm pitch)
- **Operating Temperature**: -40°C to +85°C
- **Manufacturer**: STMicroelectronics
- **Part Number**: LIS3DHTR

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | VDD_IO | Digital interface power supply |
| 4 | SCL/SPC | I²C clock / SPI clock |
| 5 | GND | Ground |
| 6 | SDA/SDI/SDO | I²C data / SPI data |
| 7 | SDO/SA0 | SPI data out / I²C address select |
| 8 | CS | SPI chip select |
| 9 | INT2 | Interrupt 2 output |
| 10 | RES | Reserved (leave unconnected) |
| 11 | INT1 | Interrupt 1 output |
| 12 | GND | Ground |
| 13 | ADC3 | Auxiliary ADC input 3 |
| 14 | VDD | Analog power supply |
| 15 | ADC2 | Auxiliary ADC input 2 |
| 16 | ADC1 | Auxiliary ADC input 1 |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
