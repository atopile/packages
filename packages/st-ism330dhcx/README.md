# STMicroelectronics ISM330DHCX 6-Axis IMU with Machine Learning Core

Advanced system-in-package featuring a 3D digital accelerometer and 3D digital gyroscope with embedded machine learning capabilities and auxiliary SPI interface for external sensors.

## Features

- **6-Axis Motion Sensing**: 3D accelerometer + 3D gyroscope
- **Machine Learning Core**: On-chip ML capabilities for pattern recognition
- **Wide Dynamic Range**: Accelerometer ±2g/±4g/±8g/±16g, Gyroscope ±125/±250/±500/±1000/±2000 dps
- **High Performance**: Up to 6.4 kHz ODR for accelerometer, up to 6.4 kHz for gyroscope
- **Auxiliary SPI**: Master interface for external sensors (magnetometer, pressure, etc.)
- **Dual Interface**: I²C and SPI digital output interfaces
- **Advanced Features**: FIFO, interrupts, activity recognition, pedometer
- **Ultra-Low Power**: Down to 0.55 mA in high-performance mode
- **Wide Supply Range**: 1.71V to 3.6V supply voltage

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C
import ElectricLogic

from "atopile/st-ism330dhcx/st-ism330dhcx.ato" import ST_ISM330DHCX

module Usage:
    """
    Minimal usage example for st-ism330dhcx.

    This example demonstrates basic I²C connection and interrupt usage
    for the ISM330DHCX 6-axis IMU with embedded machine learning.
    """

    sensor = new ST_ISM330DHCX

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

    # Set I²C address to 0x6A (SA0 pulled low)
    assert sensor.i2c.address is 0x6A

    # Optional: Connect external sensor via auxiliary SPI
    # external_magnetometer_cs = new ElectricLogic
    # external_magnetometer_cs ~ sensor.aux_spi_cs

```

## Applications

- **Robotics**: Robot navigation and stabilization
- **Drones**: Flight control and attitude estimation
- **Gaming**: Motion controllers and VR tracking
- **IoT**: Smart home and industrial automation
- **Fitness**: Activity recognition and step counting
- **Automotive**: Electronic stability programs
- **AR/VR**: Head tracking and gesture recognition
- **Industrial**: Vibration monitoring and condition monitoring

## Machine Learning Features

- **Embedded ML Core**: On-chip machine learning engine
- **Pattern Recognition**: Real-time classification without external processing
- **Activity Detection**: Walking, running, stationary state recognition
- **Gesture Recognition**: Custom gesture training and detection
- **Anomaly Detection**: Unusual motion pattern identification
- **Power Efficiency**: ML processing without waking main CPU

## Interface Options

### I²C Interface
- **Clock Speed**: Up to 1MHz (Fast Mode Plus)
- **Address**: 0x6A (SA0=0) or 0x6B (SA0=1)
- **Multi-byte**: Automatic address increment

### SPI Interface
- **Speed**: Up to 10MHz
- **Mode**: Mode 0 and Mode 3
- **CS**: Active low chip select

### Auxiliary SPI Interface
- **External Sensors**: Connect magnetometer, pressure sensor, etc.
- **Master Mode**: ISM330DHCX acts as SPI master
- **Data Hub**: Synchronized data from multiple sensors

## Interrupt Features

- **INT1 & INT2**: Two independent interrupt pins
- **Configurable Events**: Motion detection, free-fall, orientation, ML events
- **Data Ready**: Accelerometer and gyroscope data ready signals
- **FIFO Events**: Watermark, full, overrun interrupts
- **ML Interrupts**: Machine learning core decision outputs

## Performance Specifications

### Accelerometer
- **Full Scale**: ±2g, ±4g, ±8g, ±16g
- **Sensitivity**: 0.061 mg/LSB @ ±2g
- **Noise**: 60 µg/√Hz
- **ODR**: 12.5 Hz to 6.4 kHz

### Gyroscope
- **Full Scale**: ±125, ±250, ±500, ±1000, ±2000 dps
- **Sensitivity**: 4.375 mdps/LSB @ ±125 dps
- **Noise**: 7 mdps/√Hz
- **ODR**: 12.5 Hz to 6.4 kHz

## Package Information

- **JLCPCB Part Number**: C2655101
- **Package**: LGA-14 (3mm × 2.5mm, 0.5mm pitch)
- **Operating Temperature**: -40°C to +85°C
- **Manufacturer**: STMicroelectronics
- **Part Number**: ISM330DHCXTR

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | SDO/SA0 | SPI data out / I²C address select |
| 2 | SDX | Auxiliary SPI data input |
| 3 | SCX | Auxiliary SPI clock |
| 4 | INT1 | Interrupt 1 output |
| 5 | VDD_IO | Digital interface power supply |
| 6 | GND | Ground |
| 7 | GND | Ground |
| 8 | VDD | Analog power supply |
| 9 | INT2 | Interrupt 2 output |
| 10 | OCS_AUX | Auxiliary SPI chip select output |
| 11 | SDO_AUX | Auxiliary SPI data output |
| 12 | CS | Main SPI chip select |
| 13 | SCL | I²C clock / Main SPI clock |
| 14 | SDA | I²C data / Main SPI data input |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
