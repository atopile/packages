# Maxim DS18B20 1-Wire Digital Temperature Sensor

The **Maxim DS18B20** is a programmable resolution 1-Wire digital thermometer that provides 9-bit to 12-bit Celsius temperature measurements. The DS18B20 communicates over a 1-Wire bus that by definition requires only one data line (and ground) for communication with a central microprocessor. It has an operating temperature range of -55°C to +125°C and is accurate to ±0.5°C over the range of -10°C to +85°C.

## Build Targets
This package has several build targets listed below. Each build target has a different physical package.

| Package | Module         | Build Target   |
|---------|----------------|----------------|
| TO-92   | Maxim_DS18B20  | maxim-ds18b20  |
| MSOP-8  | Maxim_DS18B20U | maxim-ds18b20u |
| SOIC-8  | Maxim_DS18B20Z | maxim-ds18b20z |

## Ato Module Exposed Interfaces

| Interface | Description |
|-----------|-------------|
| `power`   | Power supply rail (VDD/GND) - 3V to 5.5V |
| `data_line` | 1-Wire data communication line (DQ pin) requires external 4.7kΩ pull-up |

## Usage Example
```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import ElectricLogic
import Resistor

from "atopile/maxim-ds18b20/maxim-ds18b20.ato" import Maxim_DS18B20
from "atopile/maxim-ds18b20/maxim-ds18b20.ato" import Maxim_DS18B20U
from "atopile/maxim-ds18b20/maxim-ds18b20.ato" import Maxim_DS18B20Z

module Usage:
    """
    Minimal usage example for Maxim DS18B20 1-Wire Digital Temperature Sensor.

    The DS18B20 is connected to a microcontroller via a single 1-Wire data line.
    The sensor includes an internal 4.7kΩ pull-up resistor to VDD automatically.
    """

    # Power supply (3.3V)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    # DS18B20 temperature sensor instance
    temp_sensor_to92 = new Maxim_DS18B20
    temp_sensor_msop8 = new Maxim_DS18B20U
    temp_sensor_soic8 = new Maxim_DS18B20Z

    # 1-Wire data line interface
    onewire_data = new ElectricLogic
    onewire_data.reference ~ power_3v3

    # --- 1-Wire bus pull-up resistor ---
    pullup_resistor = new Resistor
    pullup_resistor.resistance = 4.7kohm +/- 5%
    pullup_resistor.package = "0402"
    onewire_data.line ~> pullup_resistor ~> power_3v3.hv

    # Power distribution
    power_3v3 ~ temp_sensor_to92.power
    power_3v3 ~ temp_sensor_msop8.power
    power_3v3 ~ temp_sensor_soic8.power

    # Connect 1-Wire data line
    onewire_data ~ temp_sensor_to92.data_line
    onewire_data ~ temp_sensor_msop8.data_line
    onewire_data ~ temp_sensor_soic8.data_line

```

## License

Released under the [MIT License](https://opensource.org/license/mit).
