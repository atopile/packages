# Texas Instruments BQ25185 Li-Ion/Li-Pol Battery Charger

The BQ25185 is a highly integrated 1A single-input, single-cell Li-Ion and Li-Pol battery charger with integrated power path management. It provides a compact charging solution for space-constrained portable applications.

## Features

- **1A Programmable Charge Current**: Adjustable via external resistor
- **Wide Input Voltage Range**: 3V to 18V input support
- **Integrated Power Path**: Simultaneous charging and system power
- **Smart Power Management**: Dynamic Power Management (DPM) with input current limiting
- **Battery Protection**: Over-voltage, under-voltage, and thermal protection
- **Temperature Monitoring**: NTC thermistor support for safe charging
- **Dual Status Outputs**: Charge and fault status indication
- **Programmable Settings**: Battery regulation voltage and input current limits
- **Factory Mode**: Production testing support
- **Small Package**: 2.2×2.0 mm WSON-10 package

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")

import ElectricPower
import Resistor

from "ti-bq25185.ato" import TI_BQ25185

module Usage:
    """
    Minimal usage example for TI BQ25185 battery charger.
    Shows basic configuration for charging a single-cell Li-Ion battery with USB input.
    """

    charger = new TI_BQ25185

    # Input power (USB 5V)
    power_usb = new ElectricPower
    power_usb ~ charger.power_input
    assert power_usb.voltage within 4.75V to 5.25V

    # System power output (for powering the device)
    power_system = new ElectricPower
    power_system ~ charger.power_system

    # Battery connection (single-cell Li-Ion)
    power_battery = new ElectricPower
    power_battery ~ charger.power_battery
    # Typical Li-Ion voltage range
    assert power_battery.voltage within 3.0V to 4.2V

    # Temperature sensing with 10kΩ NTC thermistor
    temp_sensor = new Resistor
    temp_sensor.resistance = 10kohm +/- 5%
    temp_sensor.package = "0402"
    charger.temp_sense.line ~> temp_sensor ~> power_system.lv

    # Charge configuration (default values set by resistors in module)
    # - Input current limit: 500mA (set by 18kΩ ILIM_VSET resistor)
    # - Battery regulation voltage: 4.2V (set by 18kΩ ILIM_VSET resistor)
    # - Charge current: depends on ISET resistor value

    # Status LEDs can be connected to status_1 and status_2 pins
    # status_1: Fault indication (active low)
    # status_2: Charge status (active low during charging)
```

## Hardware Features

### Power Management
- **Input Voltage**: 3V to 18V (VBUS)
- **System Output**: 1.8V to 4.5V (SYS)
- **Battery Voltage**: 1.8V to 4.4V (BAT)
- **Charge Current**: Up to 1A (programmable)
- **Power Path**: Integrated management for simultaneous charging and system operation

### Configuration Resistors
- **ISET Resistor**: Sets charge current limit
  - Formula: R_ISET = 300kΩ·A / I_CHARGE
  - Example: For 500mA → R_ISET = 600kΩ
- **ILIM_VSET Resistor**: Sets input current limit and battery regulation voltage
  - Lookup table from datasheet determines values
  - Default: 18kΩ (500mA input limit, 4.2V battery regulation)

### Status and Control
- **nCE Pin**: Charge enable (active low)
- **STAT1**: Fault status output (open-drain, active low)
- **STAT2**: Charge status output (open-drain, active low)
- **TS_MR**: Temperature sensing and manual reset

### Protection Features
- **Thermal Protection**: Automatic charge current reduction and shutdown
- **Input Over-voltage Protection**: Up to 22V absolute maximum
- **Battery Over-voltage Protection**: Prevents battery damage
- **Short Circuit Protection**: System and battery short protection
- **Reverse Current Protection**: Prevents battery discharge through input

## Configuration Examples

### Common ILIM_VSET Resistor Values
| Resistor (kΩ) | Input Current Limit | Battery Regulation Voltage |
|---------------|--------------------|-----------------------------|
| 130           | 500mA              | 4.1V                       |
| 100           | 1100mA             | 4.1V                       |
| 75            | 500mA              | 4.4V                       |
| 56            | 1100mA             | 4.4V                       |
| 24            | 100mA              | 4.2V                       |
| 18            | 500mA              | 4.2V                       |
| 13            | 1100mA             | 4.2V                       |

### Charge Current Setting (ISET Resistor)
| Target Current | ISET Resistor |
|----------------|---------------|
| 100mA          | 3.0MΩ         |
| 250mA          | 1.2MΩ         |
| 500mA          | 600kΩ         |
| 750mA          | 400kΩ         |
| 1000mA         | 300kΩ         |

## Applications

### Portable Electronics
- Smartphones and tablets
- Wearable devices
- Bluetooth headphones and earbuds
- Portable gaming devices

### IoT and Connected Devices
- Smart sensors and monitors
- Wireless communication modules
- GPS trackers
- Remote monitoring equipment

### Industrial Applications
- Handheld test equipment
- Portable medical devices
- Industrial scanners
- Battery-powered tools

## Status Indication

### STAT1 and STAT2 Pin States
| STAT1 | STAT2 | Status |
|-------|-------|--------|
| Hi-Z  | Hi-Z  | No input power |
| Low   | Hi-Z  | Input fault |
| Hi-Z  | Low   | Charging |
| Hi-Z  | Hi-Z  | Charge complete |
| Low   | Low   | Sleep mode |

## Technical Specifications

- **Package**: WSON-10 (2.2×2.0×0.6 mm)
- **Operating Temperature**: -40°C to 85°C
- **Charge Accuracy**: ±1% (typical)
- **Input Current Regulation**: ±10% (typical)
- **Thermal Regulation**: 120°C (typical)
- **Standby Current**: <1µA (typical)
- **Switching Frequency**: 1.2MHz (internal)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
