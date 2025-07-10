# ISSI IS31FL3731 LED Matrix Driver

12×8 (144) LED matrix driver with PWM control and I²C interface.

## Usage

```ato
import ElectricPower, I2C
from "issi-is31fl3731.ato" import ISSI_IS31FL3731

module Example:
    rail = new ElectricPower
    rail.voltage = 3.3V

    bus = new I2C

    driver = new ISSI_IS31FL3731
    rail ~ driver.power
    bus ~ driver.i2c
```

`driver.interrupt` can be wired to an MCU GPIO for frame-sync or
interrupt-driven events. Tie the column/row outputs to your LED matrix as
needed.

## Contributing
Contributions are welcome! Feel free to open issues or PRs.

## License
MIT
