# ADI ADXL345 3-Axis Digital Accelerometer

A comprehensive atopile package for the Analog Devices ADXL345 3-axis digital accelerometer with I2C and SPI interfaces.

## Features

- **3-axis accelerometer** with selectable measurement ranges: ±2g, ±4g, ±8g, ±16g
- **High resolution**: 13-bit resolution up to ±16g
- **Dual interfaces**: I2C and SPI digital communication
- **Ultra-low power**: 23μA in measurement mode, 0.1μA in standby
- **Interrupt outputs**: Two configurable interrupt pins for motion detection, free-fall, etc.
- **Wide operating voltage**: 2.0V to 3.6V (VS), 1.7V to 3.6V (VDD_IO)
- **High sampling rate**: Up to 3200 Hz output data rate

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
import ElectricPower
import I2C

from "atopile/adi-adxl345/adi-adxl345.ato" import ADI_ADXL345

module Usage:
    """
    Minimal usage example for ADI ADXL345 3-axis digital accelerometer.
    Shows basic I2C connection with power supply and interrupt usage.
    """

    # Power rail (3.3 V shared for core & I/O)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I2C bus
    i2c_bus = new I2C

    # Accelerometer instance
    accelerometer = new ADI_ADXL345

    # Connect required power rails
    power_3v3 ~ accelerometer.power_vs
    power_3v3 ~ accelerometer.power_io

    # Provide logic reference for the bus
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # Connect I2C bus
    i2c_bus ~ accelerometer.i2c

    # I2C address is fixed at 0x53 (SDO pin tied to GND)
```

## Hardware Features

### Power Supply
- **VS (Sensor Core)**: 2.0V to 3.6V
- **VDD_IO (Digital I/O)**: 1.7V to 3.6V
- Integrated decoupling capacitors (100nF on both rails)

### Communication
- **I2C Interface**: Fixed 7-bit address 0x53 (SDO pin tied to GND)
- **SPI Interface**: 3-wire or 4-wire SPI modes supported
- Built-in I2C pull-up resistors (10kΩ)

### Interrupts
- Two interrupt outputs (INT1, INT2)
- Configurable for data ready, motion detection, free-fall, etc.

### Address Configuration
- **Fixed I2C Address**: 0x53
- SDO/ALT_ADDRESS pin is tied to GND for consistent addressing
- For alternative address (0x1D), modify the package to tie SDO to VDD_IO

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
