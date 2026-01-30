# Texas Instruments INA237 85V 16-bit DC Current/Voltage/Power Monitor

High-precision digital power monitor with 16-bit delta-sigma ADC designed for current-sensing applications. The INA237 supports up to 85V common-mode voltage measurement and provides I2C digital interface for easy integration.

## Key Features

- **Wide voltage range**: -0.3V to +85V common-mode voltage support
- **High precision**: 16-bit delta-sigma ADC with ±0.3% gain error
- **Flexible measurement**: ±163.84mV or ±40.96mV full-scale differential input
- **I2C interface**: 16 selectable addresses (0x40-0x4F) with 2.94MHz high-speed support
- **Integrated temperature sensor**: ±1°C accuracy for die temperature measurement
- **Low power**: 640µA typical operating current, 5µA max shutdown current
- **Supply voltage**: 2.7V to 5.5V operating range
- **Package**: 10-VSSOP package, -40°C to +125°C operating temperature

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("MODULE_TEMPLATING")
import I2C
import ElectricPower
import ElectricLogic
import Resistor
from "atopile/ti-ina237/ti-ina237.ato" import TI_INA237

module Usage:
    """
    Minimal usage example for ti-ina237.
    Demonstrates basic current monitoring setup with shunt resistor
    """

    # Create the INA237 power monitor
    power_monitor = new TI_INA237
    power_monitor.max_current = 1A  # Set maximum expected current

    # System power supplies
    system_3v3 = new ElectricPower
    system_3v3.voltage = 3.3V +/- 5%

    load_power = new ElectricPower
    load_power.voltage = 3.3V +/- 5%

    # I2C bus
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # Connect power monitor to system
    system_3v3 ~ power_monitor.power
    i2c_bus ~ power_monitor.i2c

    # Connect bus voltage sensing to load power supply
    power_monitor.vbus.line ~ load_power.hv
    power_monitor.vbus.reference ~ system_3v3

    # Connect current sensing through built-in shunt resistor
    # Current flows: load_power.hv -> power_monitor (with internal shunt) -> load_power.lv
    load_power.hv ~ power_monitor.current_sense.p.line
    power_monitor.current_sense.n.line ~ load_power.lv

    # Set I2C address to 0x40 (base address when A1=0, A0=0)
    # Address pins will be pulled down internally or externally
    power_monitor.i2c.address = 0x40

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
