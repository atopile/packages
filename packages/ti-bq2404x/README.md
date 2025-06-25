# BQ2404XDSQR 1A 1S Battery Charger

Input Voltage: 4.45V - 6.45V
Charge termination Voltage: 4.20V/4.35V

## Usage

```ato
import Battery
import PoweredLED
import Resistor

from "atopile/ti-bq2404x/bq2404x.ato" import BQ24040DSQR

module Test:
    """
    Test module for BQ24040DSQR
    """
    charger = new BQ24040DSQR

    battery = new Battery
    battery.voltage = 4.2V
    battery.capacity = 300mAh

    # Configure charge current to 1C
    charger.charge_current = battery.capacity / 1h +/- 10%

    # Connect power
    power = new ElectricPower
    power.voltage = 5V
    power ~ charger.power_in
    charger.power_batt ~ battery.power

    # Charge indicator
    charge_led = new PoweredLED
    power.vcc ~> charge_led ~> charger.charge_status.line
    charge_led.current_limiting_resistor.resistance = 10ohm +/- 10%
    charge_led.led.lcsc_id = "C2288"

    # Power good indicator
    power_good_led = new PoweredLED
    power.vcc ~> power_good_led ~> charger.power_good.line
    power_good_led.current_limiting_resistor.resistance = 10ohm +/- 10%
    power_good_led.led.lcsc_id = "C12624"

    # Temperature sensor - 10k ohm NTC
    temp_sensor = new Resistor
    temp_sensor.lcsc_id = "C2892547"
    charger.temperature_sense.line ~> temp_sensor ~> power.gnd


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
