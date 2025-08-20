# Bosch BME280 – Temperature, Humidity & Pressure Sensor

Atopile driver for the **Bosch Sensortec BME280** digital environmental sensor (LCSC part **C92489**).  The device measures temperature, relative humidity, and barometric pressure and supports both I²C (default) and SPI interfaces.  Two separate supplies are required: **VDD** (sensor core, 1.71 V – 3.6 V) and **VDDIO** (digital I/O, 1.2 V – 3.6 V).  I²C addresses **0x76** or **0x77** are selected via the SDO pin.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Standard library imports ---
import ElectricPower
import I2C

# --- Package import ---
from "atopile/bosch-bme280/bosch-bme280.ato" import Bosch_BME280


module Usage:
    """
    Minimal usage example for `bosch-bme280`.
    Powers the BME280 from a 3 V 3 rail and places it on an I²C bus at the
    default address **0x76**.
    """

    # Power rail (3.3 V shared for core & I/O)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    # I²C bus
    i2c_bus = new I2C

    # Sensor instance
    sensor = new Bosch_BME280

    # Connect required power rails
    power_3v3 ~ sensor.power_core
    power_3v3 ~ sensor.power_io

    # Provide logic reference for the bus
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # Connect I²C bus
    i2c_bus ~ sensor.i2c

    # (Optional) Select address – defaults to 0x76 (SDO=0)
    sensor.i2c.address = 0x76

```

## Contributing

Contributions are welcome! Please open an issue or pull request and ensure the `usage` build target passes (`ato build usage`).

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
