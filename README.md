# stemma_connectors

STEMMA QT connector (vertical)

Usage:

```ato
import ElectricPower
import I2C

from "atopile/stemma_connectors/main.ato" import StemmaQTVertical

module Example:
    power = new ElectricPower
    power.voltage = 3.3V +/- 5%

    i2c = new I2C

    stemma_qt_vertical = new StemmaQTVertical
    i2c ~ stemma_qt_vertical.i2c
    power ~ stemma_qt_vertical.power
```