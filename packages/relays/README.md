# Relays

Contains a DPDT relay (HFD4_5) with logic level driver circuit and LED indicator

## Usage

```ato

import I2C
import Power

from "atopile/relays/relays.ato" import PowerRelay


module Test:
    # make a relay
    power_relay = new PowerRelay

    # Power interfaces to switch
    power_in = new ElectricPower
    power_out = new ElectricPower

    # Control signal
    control = new ElectricSignal

    # Power for relay coil
    power_5v = new ElectricPower

    # Connect control signal to relay
    control ~> power_relay.control
    # Driving control signal high will turn on the relay (>2.5V)
    # Driving control signal low will turn off the relay (<1V)

    # Connect power_5v to relay power
    power_5v ~> power_relay.power

    # Connect power_in to power_out via switch
    power_in ~> power_relay.switch ~> power_out


```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
