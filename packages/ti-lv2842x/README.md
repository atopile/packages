The LV2841 and LV2842 are PWM DC/DC buck (stepdown) regulators. With a wide input range from 4V-40V, they are suitable for a wide range of application from industrial to automotive for power conditioning from unregulated source.

## Usage

```ato
import ElectricPower

from "atopile/ti-lv2842x/ti-lv2842x.ato" import TI_LV2842X

module Usage:
    """
    Test design — independent regulators to avoid cross-regulator solver dependencies.
    """

    power_24v = new ElectricPower
    assert power_24v.voltage within 24V +/- 10%
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%
    regulator_24_3v3 = new TI_LV2842X
    regulator_24_3v3.power_in ~ power_24v
    regulator_24_3v3.power_out ~ power_3v3
    regulator_24_3v3.power_out.max_current = 200mA
    assert regulator_24_3v3.feedback_divider.current within 10uA to 100uA
```
