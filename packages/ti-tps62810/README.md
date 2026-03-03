# Texas Instruments TPS62810-Q1 Step-Down Converter

2.75V to 6V input, 0.6V to 5.5V adjustable output, 4A synchronous buck converter with 1.8MHz to 4MHz adjustable switching frequency.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
import ElectricPower
import ElectricLogic
from "atopile/ti-tps62810/ti-tps62810.ato" import TI_TPS62810

module MyDesign:
    regulator = new TI_TPS62810
    regulator.power_out.max_current = 4000mA

    power_in = new ElectricPower
    assert power_in.voltage within 3.3V +/- 5%
    power_out = new ElectricPower
    assert power_out.voltage within 1.8V +/- 3%

    power_in ~ regulator.power_in
    regulator.power_out ~ power_out

    # Enable — tie to input for always-on
    enable = new ElectricLogic
    enable.line ~ power_in.hv
    regulator.enable ~ enable

    # MODE/SYNC — tie high for forced PWM
    mode = new ElectricLogic
    mode.line ~ power_in.hv
    regulator.mode_sync ~ mode
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
