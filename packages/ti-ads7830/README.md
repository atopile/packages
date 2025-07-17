# TI ADS7830 8-bit, 8-Channel I²C ADC

The TI ADS7830 is an 8-bit, 8-channel analog-to-digital converter with an I²C interface, internal 2.5V reference, and 70kHz sampling rate. It features 4 differential or 8 single-ended input channels and operates from 2.7V to 5.0V supply voltage.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

# --- Imports ---
import ElectricPower
import I2C

from "ti-ads7830.ato" import TI_ADS7830

module Usage:
    """
    Minimal usage example for ti-ads7830.
    Demonstrates connecting power and I2C to the ADS7830 ADC.
    """

    # --- Power supply ---
    power = new ElectricPower
    power.voltage = 3.3V +/- 5%

    # --- I2C bus ---
    i2c_bus = new I2C
    i2c_bus.frequency = 400kHz

    # --- ADC instance ---
    adc = new TI_ADS7830

    # --- Connections ---
    power ~ adc.power
    i2c_bus ~ adc.i2c

    # --- Set I2C address (optional - default is 0x48) ---
    # i2c_bus.address = 0x48
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
