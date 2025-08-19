# ST VL53L4CX Time-of-Flight Distance Sensor

Short-range ToF proximity sensor capable of measuring distances from
**≈1 mm up to 1.3 m** with 1 mm resolution.
Communicates over **I²C** (default address `0x29`).
Packaged in a tiny 4.4 × 2.4 mm **LGA-12** module.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/st-vl53l4cx/st-vl53l4cx.ato" import ST_VL53L4CX

module MCU:
    """Host MCU providing 3 V rail and I²C bus."""
    power = new ElectricPower
    i2c = new I2C

module Usage:
    """Minimal usage example for the ST_VL53L4CX sensor."""

    mcu = new MCU
    tof_sensor = new ST_VL53L4CX

    # Shared power rail
    rail = new ElectricPower
    rail.voltage = 3.3V
    rail ~ mcu.power
    rail ~ tof_sensor.power

    # I²C connection
    mcu.i2c ~ tof_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
