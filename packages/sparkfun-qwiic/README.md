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

module MCU:
    """Host MCU providing I²C bus and power rail."""

    power = new ElectricPower
    i2c = new I2C


module Usage:
    """Minimal example showcasing both SparkFun Qwiic connector variants."""

    # MCU & connectors
    mcu = new MCU
    qwiic_vertical = new QwiicVertical
    qwiic_horizontal = new QwiicHorizontal

    # --- I²C bus ---
    i2c = new I2C

    # Shared 3V3 rail
    power = new ElectricPower
    power.voltage = 3.3V
    power ~ mcu.power
    power ~ qwiic_vertical.power
    power ~ qwiic_horizontal.power

    # I²C bus wiring
    i2c ~ qwiic_vertical.i2c
    i2c ~ qwiic_horizontal.i2c
    i2c ~ mcu.i2c

    # --- I²C pull-up resistors ---
    pullup_resistors = new Resistor[2]
    for resistor in pullup_resistors:
        resistor.value = 10k +/- 1%
        resistor.package = "0402"
    i2c.scl.line ~> pullup_resistors[0] ~> i2c.scl.reference.hv
    i2c.sda.line ~> pullup_resistors[1] ~> i2c.sda.reference.hv
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
