# Sensirion SHT31-DIS – Temperature & Humidity Sensor

Atopile driver for the **Sensirion SHT31-DIS-B2.5kS** digital temperature and humidity sensor (LCSC part **C80862**).  The device communicates over I²C, supports two selectable 7-bit addresses (**0x44** / **0x45**), and operates from a single **2.4 V – 5.5 V** rail.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Standard library imports ---
import ElectricPower
import I2C

# --- Package import ---
from "atopile/sensirion-sht31/sensirion-sht31.ato" import Sensirion_SHT31


module Usage:
    """
    Minimal usage example for `sensirion-sht31`.
    Powers the SHT31 from a 3 V 3 rail and connects it to an I²C bus using the
    default address **0x44** (ADDR pin low).
    """

    # Power rail (3.3 V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I²C bus
    i2c_bus = new I2C

    # Sensor instance
    sensor = new Sensirion_SHT31

    # Connect power rail
    power_3v3 ~ sensor.power

    # Provide logic reference for the bus
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # Connect I²C bus
    i2c_bus ~ sensor.i2c

    # (Optional) Select address – defaults to 0x44 (ADDR=0)
    sensor.i2c.address = 0x44

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
