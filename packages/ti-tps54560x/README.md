# TI TPS54560x Buck Converter

## Usage

```ato
from "atopile/ti-tps54560x/ti-tps54560x.ato" import TPS54560x

// Example usage in your design
module Test5V:
    regulator = new TPS54560x
    regulator.v_in = 24V +/- 10%
    regulator.v_out = 5V +/- 5%

    enable = new ElectricLogic
    enable.line ~ regulator.power_in.vcc # enable active high
    regulator.enable ~ enable
```

## License

This package is released under the MIT License.

## Author

Created by Narayan Powderly <narayan@atopile.io>
