# Maxim DS3231 Real-Time Clock (RTC) with Integrated Crystal & TCXO

This package provides an Atopile driver for the **Maxim Integrated DS3231** extremely-accurate I²C real-time clock.

Features:

- Built-in 32.768 kHz crystal and temperature-compensated oscillator
- Battery-backed time-keeping (VBAT pin)
- 236 B SRAM, two alarms, square-wave output
- Operating voltage 2.3 V – 5.5 V
- Fixed 7-bit I²C address `0x68`

## Usage

```ato
#pragma experiment("FOR_LOOP")
#pragma experiment("TRAITS")

import ElectricPower
import I2C
import ElectricLogic
import has_part_removed
from "atopile/maxim-ds3231/maxim-ds3231.ato" import Maxim_DS3231
from "parts/Q_J_CR1220_2/Q_J_CR1220_2.ato" import Q_J_CR1220_2_package

module MCU:
    """Host microcontroller providing I²C bus and 3.3 V rail."""

    trait has_part_removed

    power = new ElectricPower
    i2c = new I2C
    irq = new ElectricLogic

module Usage:
    """Minimal usage example for Maxim DS3231 RTC."""

    # Instantiate MCU and RTC
    mcu = new MCU

    # Shared 3.3 V rail
    power = new ElectricPower
    power.voltage = 3.3V +/- 5%

    # Backup battery holder (CR1220 coin cell)
    battery_holder = new Q_J_CR1220_2_package

    backup_rail = new ElectricPower
    backup_rail.voltage = 3.0V +/- 10%

    # Connect battery holder to backup rail
    backup_rail.hv ~ battery_holder.1
    backup_rail.lv ~ battery_holder.2

    rtc = new Maxim_DS3231

    # Power distribution
    power ~ mcu.power
    power ~ rtc.power

    # I²C connection
    mcu.i2c ~ rtc.i2c

    # Optional interrupt line
    rtc.square_interrupt ~ mcu.irq

    # Connect backup rail to RTC
    backup_rail ~ rtc.backup_power
```

## Contributing

Pull requests are welcome — feel free to improve the model, add examples, or refine parameters.

## License

MIT
