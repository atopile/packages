# nxp-pca9685

Atopile package for the NXP PCA9685, a 16-channel 12-bit PWM controller
driven over I2C. Same chip used on the Adafruit 16-channel PWM/Servo
breakout, so it's useful for driving hobby servos or dimming LEDs when you
run out of timer channels on the MCU.

Part used: `PCA9685PW,118`, TSSOP-28, LCSC `C57442`.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/nxp-pca9685/nxp-pca9685.ato" import NXP_PCA9685


module Usage:
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V

    i2c_bus = new I2C

    pwm = new NXP_PCA9685

    power_3v3 ~ pwm.power
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference
    i2c_bus ~ pwm.i2c

    # Default address is 0x40 - same as the Adafruit breakout.
    pwm.i2c.address = 0x40
```

## What the module does for you

- Exposes typed interfaces: `power`, `i2c`, `output_enable`, `extclk`, and
  `led[0:15]`.
- Includes 4.7k I2C pull-ups (sized for Fm+ at 3.3V / 5V).
- Adds a 10k pull-up on `nOE` so the outputs default to disabled on power-up.
  This matters for servos - you don't want them jerking to an undefined
  position while the MCU is still booting.
- Adds a 100k pull-down on `EXTCLK` so the pin isn't floating when you use
  the internal 25 MHz oscillator.
- Places 100nF + 10uF decoupling near the part. The 10uF is there because
  16 outputs switching in phase pulls a noticeable current spike.
- Asserts `power.voltage` is in 2.3V..5.5V per the datasheet.
- Uses a 6-bit `Addressor` so you can put up to 62 of these on one bus.

## Servo driver example

The chip's supply (`power`) is separate from the servo rail. For anything
more than one or two micro servos you want a beefy 5V or 6V BEC powering
the servo headers.

```ato
from "atopile/nxp-pca9685/nxp-pca9685.ato" import NXP_PCA9685

module ServoShield:
    power_logic = new ElectricPower  # 3.3V or 5V logic
    power_servo = new ElectricPower  # 5-6V BEC to the servo headers
    i2c_bus     = new I2C

    driver = new NXP_PCA9685
    driver.power ~ power_logic
    driver.i2c   ~ i2c_bus

    # driver.led[i].line goes to each servo header signal pin.
    # Servo header V+ to power_servo.hv, GND to power_servo.lv.
```

## Notes

- The datasheet calls the output enable pin `/OE` (active low). The EasyEDA
  symbol exports it as `OE`. In this package it's wired as `package.nOE`.
- `EXTCLK` is optional. Leave the `extclk` interface unconnected and the
  chip uses its internal oscillator.
- I2C is Fast-mode Plus capable (up to 1 MHz). The default 4.7k pull-ups are
  fine for typical boards; drop them on long buses or when many devices
  share the line.
- Supply is 2.3V to 5.5V. The `assert` in the module will fail the build if
  you wire something outside that range.

## Related

- `PCA9685BS,118` is the same die in HVQFN-28 (LCSC `C110059`). Open an
  issue if you want that variant added.
- `TLC59711` is a 12-channel, 16-bit PWM over SPI if you need more
  resolution but fewer channels.

## License

MIT.
