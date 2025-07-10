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
from "maxim-ds3231.ato" import Maxim_DS3231
import ElectricPower, I2C

module Demo:
    rail_3v3 = new ElectricPower
    rail_3v3.voltage = 3.3V

    bus = new I2C
    rtc = new Maxim_DS3231

    rail_3v3 ~ rtc.power
    bus ~ rtc.i2c
```

## Contributing
Pull requests are welcome — feel free to improve the model, add examples, or refine parameters.

## License
MIT
