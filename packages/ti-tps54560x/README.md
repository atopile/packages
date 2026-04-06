# TI TPS54560x Buck Converter

## Usage

```ato
import ElectricLogic
import ElectricPower

from "atopile/ti-tps54560x/ti-tps54560x.ato" import TI_TPS54560

module Usage:
    """Example usage of TI TPS54560x Buck Converter"""

    # Power rails
    power_24v = new ElectricPower
    power_5v = new ElectricPower

    # Buck converter
    regulator = new TI_TPS54560

    # Configure input/output voltages
    assert power_24v.voltage within 24V +/- 10%
    assert power_5v.voltage within 5V +/- 5%

    # Connect power
    power_24v ~ regulator.power_in
    regulator.power_out ~ power_5v

    # Enable control (tie to input voltage for always-on)
    enable = new ElectricLogic
    enable.line ~ power_24v.hv
    enable.reference ~ power_24v
    regulator.enable ~ enable

```

## License

This package is released under the MIT License.

## Author

Created by Narayan Powderly <narayan@atopile.io>
