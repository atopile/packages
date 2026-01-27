# Texas Instruments LM1117 800mA Low-Dropout Linear Regulator

The LM1117 is an 800mA low-dropout linear regulator with adjustable output voltage from 1.25V to 13.8V. It features current limiting, thermal overload protection, and requires only a 1uF output capacitor for stability.

## Features

- Adjustable output voltage: 1.25V to 13.8V
- Output current: up to 800mA
- Input voltage range: 2.7V to 15V
- Low dropout voltage: 1.2V typical at 800mA
- 1.25V internal reference voltage
- Current limiting and thermal protection
- SOT-223 package

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import has_part_removed

from "atopile/ti-lm1117/ti-lm1117.ato" import TI_LM1117

module MCU:
    """Host MCU requiring 3.3V power rail."""

    trait has_part_removed

    power = new ElectricPower
    assert power.voltage within 3.3V +/- 5%


module Usage:
    """
    Minimal usage example for TI LM1117.
    Converts 5V input to 3.3V output for an MCU.
    """

    # Input power supply (e.g., from USB)
    power_5v = new ElectricPower
    assert power_5v.voltage within 5V +/- 5%

    # Output power rail
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%

    # LDO regulator
    ldo = new TI_LM1117

    # MCU load
    mcu = new MCU

    # Connections
    power_5v ~> ldo ~> power_3v3
    power_3v3 ~ mcu.power
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
