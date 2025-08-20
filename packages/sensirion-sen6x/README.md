# Sensirion SEN6X Environmental Sensor Module

The **Sensirion SEN6X** series (e.g. SEN60, SEN61, SEN62) is an integrated particulate matter, relative humidity, temperature, VOC, NOx, HCHO sensor module.
The module exposes a 6-pin JST-GH connector that provides 3.3 V power and an I²C interface.

This package provides an Atopile driver that models the module, its power requirements, basic decoupling capacitors and I²C pull-ups.
The physical footprint is represented by a *JST GH 6-pin right-angle connector* (LCSC #C133065).

## Usage

```ato
import ElectricPower
import I2C

from "atopile/sensirion-sen6x/sensirion-sen6x.ato" import Sensirion_SEN6X

module MCU:
    """Host MCU providing I²C bus and power rail."""
    power = new ElectricPower
    i2c = new I2C

module Usage:
    """Minimal example usage for Sensirion_SEN6X sensor."""

    # Instances
    mcu = new MCU
    environment_sensor = new Sensirion_SEN6X

    # Shared 3.3V rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ environment_sensor.power
    # depending on the Sensirion SEN6X model, between 75-200mA can be drawn,
    # might need a dcdc converter or separate LDO

    # I²C connection
    mcu.i2c ~ environment_sensor.i2c

```

## Contributing

Improvements and suggestions are welcome—please open an issue or pull request.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
