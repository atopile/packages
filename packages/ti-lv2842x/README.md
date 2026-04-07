The LV2841 and LV2842 are PWM DC/DC buck (stepdown) regulators. With a wide input range from 4V-40V, they are suitable for a wide range of application from industrial to automotive for power conditioning from unregulated source.

## Usage

```ato
import ElectricPower

from "atopile/ti-lv2842x/ti-lv2842x.ato" import TI_LV2842X

module Usage:
    """
    Test design — independent regulators to avoid cross-regulator solver dependencies.
    """

    # --- 36V to 15V ---
    power_36v = new ElectricPower
    assert power_36v.voltage within 36V +/- 10%
    power_15v = new ElectricPower
    assert power_15v.voltage within 15V +/- 5%
    regulator_36_15 = new TI_LV2842X
    regulator_36_15.power_in ~ power_36v
    regulator_36_15.power_out ~ power_15v
    regulator_36_15.power_out.max_current = 500mA

    # --- 12V to 5V ---
    power_12v_in = new ElectricPower
    assert power_12v_in.voltage within 12V +/- 10%
    power_5v = new ElectricPower
    assert power_5v.voltage within 5V +/- 5%
    regulator_12_5 = new TI_LV2842X
    regulator_12_5.power_in ~ power_12v_in
    regulator_12_5.power_out ~ power_5v
    regulator_12_5.power_out.max_current = 300mA

    # --- 24V to 3.3V ---
    power_24v = new ElectricPower
    assert power_24v.voltage within 24V +/- 10%
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.3V +/- 5%
    regulator_24_3v3 = new TI_LV2842X
    regulator_24_3v3.power_in ~ power_24v
    regulator_24_3v3.power_out ~ power_3v3
    regulator_24_3v3.power_out.max_current = 200mA
```
