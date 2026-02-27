# ST VL53L4CD Time-of-Flight Distance Sensor

Short-range ToF proximity sensor capable of measuring distances from
**≈1 mm up to 1.3 m** with 1 mm resolution.
Communicates over **I²C** (default address `0x29`).
Packaged in a tiny 4.4 × 2.4 mm **LGA-12** module.

## Usage

```ato
import ElectricPower
import I2C

from "atopile/st-vl53l4cd/st-vl53l4cd.ato" import ST_VL53L4CD

module Usage:
    """Minimal usage example for the ST_VL53L4CD sensor."""

    # ToF sensor
    tof_sensor = new ST_VL53L4CD

    # Power supply (3.3V typical)
    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%
    power ~ tof_sensor.power

    # I²C bus (would connect to your MCU)
    i2c = new I2C
    i2c ~ tof_sensor.i2c

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](mdc:packages/https:/opensource.org/license/mit).
