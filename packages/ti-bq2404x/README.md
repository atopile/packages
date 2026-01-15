# BQ2404XDSQR 1A 1S Battery Charger

Input Voltage: 4.45V - 6.45V
Charge termination Voltage: 4.20V/4.35V

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower, Resistor
from "atopile/ti-bq2404x/ti-bq2404x.ato" import BQ24040DSQR
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorGreen

module Usage:
    """
    5V input to 1S Li-ion charger, 500mA charge current, CHG/PG LEDs, TS 10k to GND.
    """

    charger = new BQ24040DSQR

    # Rails
    vin = new ElectricPower
    vbatt = new ElectricPower

    # Power path
    vin ~> charger ~> vbatt

    # Charge current
    charger.charge_current = 500mA +/- 10%

    # Charge status LED (active low)
    chg_led = new LEDIndicatorGreen
    vin.hv ~> chg_led ~> charger.charge_status.line

    # Power good LED (active low)
    pg_led = new LEDIndicatorGreen
    vin.hv ~> pg_led ~> charger.power_good.line

    # Temperature sense: 10k to GND
    ts_pull = new Resistor
    ts_pull.resistance = 10kohm +/- 1%
    charger.temperature_sense.line ~> ts_pull ~> vin.lv

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
