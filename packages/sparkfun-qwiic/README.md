# SparkFun Qwiic Connectors (Vertical & Horizontal)

The Qwiic ecosystem by SparkFun uses a compact 4-pin JST-SH connector to carry a 3.3V I²C bus plus power and ground.

This package provides two footprint variants:

* **QwiicVertical** – Vertical connector (JST **BM04B-SRSS-TB**, LCSC **C160390**)
* **QwiicHorizontal** – Right-angle connector (JST **SM04B-SRSS-TB**, LCSC **C160404**)

Both modules expose the required `ElectricPower` and `I2C` interfaces so you can daisy-chain Qwiic peripherals with minimal boilerplate.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")
import ElectricPower
import I2C
import Resistor

from "atopile/sparkfun-qwiic/sparkfun-qwiic.ato" import QwiicVertical
from "atopile/sparkfun-qwiic/sparkfun-qwiic.ato" import QwiicHorizontal


module Usage:
    """Minimal example showcasing both SparkFun Qwiic connector variants."""

    # Qwiic connectors
    qwiic_vertical = new QwiicVertical
    qwiic_horizontal = new QwiicHorizontal

    # --- I²C bus ---
    # Main I2C bus (would connect to microcontroller in real application)
    i2c_bus = new I2C

    # Shared 3V3 rail (would come from voltage regulator in real application)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 10%
    power_3v3 ~ qwiic_vertical.power
    power_3v3 ~ qwiic_horizontal.power

    # I²C bus wiring - daisy chain the Qwiic connectors
    i2c_bus ~ qwiic_vertical.i2c
    i2c_bus ~ qwiic_horizontal.i2c

    # --- I²C pull-up resistors ---
    i2c_bus.scl.reference ~ power_3v3
    i2c_bus.sda.reference ~ power_3v3
    pullup_resistors = new Resistor[2]
    for resistor in pullup_resistors:
        resistor.resistance = 10kohm +/- 1%
        resistor.package = "0402"
    i2c_bus.scl.line ~> pullup_resistors[0] ~> power_3v3.hv
    i2c_bus.sda.line ~> pullup_resistors[1] ~> power_3v3.hv

```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
