# ST H3LIS331 – High-G 3-Axis Accelerometer

The H3LIS331DL is a high-g, low-power, high-performance 3-axis linear
accelerometer with digital I²C/SPI serial interface standard output.
The device features ultralow-power operational modes that allow advanced power
saving and smart sleep-to-wake-up functions.
The H3LIS331DL has dynamically user-selectable full scales of ±100g/±200g/±400g
and it is capable of measuring accelerations with output data rates from 0.5 Hz to
1 kHz.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/st-h3lis331/st-h3lis331.ato" import ST_H3LIS331

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example for the ST_H3LIS331 accelerometer."""

    # MCU & sensor
    mcu = new MCU
    accelerometer = new ST_H3LIS331

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ accelerometer.power

    # I²C connection
    mcu.i2c ~ accelerometer.i2c

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the
`usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
