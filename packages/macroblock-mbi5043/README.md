# Macroblock MBI5043GP-A 16-Channel LED Driver

The Macroblock MBI5043GP-A is a high-performance 16-channel constant current LED sink driver designed for LED display applications. This package provides precise current control with excellent channel-to-channel matching and thermal management for professional LED display systems.

## Key Features

- 16 independent constant current sink outputs
- Excellent current accuracy: ±3% between channels, ±6% between ICs
- Programmable output current: 5-120mA via external resistor
- SPI-compatible serial interface for data input
- Global PWM control for brightness adjustment
- Output enable control for blanking
- Wide supply voltage range: 4.5V to 5.5V
- High-speed data transfer up to 25MHz
- Built-in thermal protection and current regulation

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")

import ElectricLogic
import ElectricPower
import Resistor

from "atopile/macroblock-mbi5043/macroblock-mbi5043.ato" import Macroblock_MBI5043
from "atopile/indicator-leds/indicator-leds.ato" import LEDIndicatorBlue

module Usage:
    """
    Minimal usage example for macroblock-mbi5043.
    Demonstrates basic LED driver configuration with serial data control.
    """

    # --- Components ---
    led_driver = new Macroblock_MBI5043

    # --- Power Supply ---
    power_5v = new ElectricPower
    """
    5V power supply for the LED driver
    """
    assert power_5v.voltage within 4.8V to 5.2V

    # --- Control Signals ---
    serial_data_input = new ElectricLogic
    """
    Serial Data Input - controlled by microcontroller GPIO
    """
    serial_data_input.reference ~ power_5v

    data_clock = new ElectricLogic
    """
    Data Clock - controlled by microcontroller GPIO
    """
    data_clock.reference ~ power_5v

    latch_enable = new ElectricLogic
    """
    Latch enable signal - controlled by microcontroller GPIO
    """
    latch_enable.reference ~ power_5v

    global_clock = new ElectricLogic
    """
    Global clock for PWM - controlled by microcontroller PWM output
    """
    global_clock.reference ~ power_5v

    # --- LED Load Examples ---
    indicator_leds = new LEDIndicatorBlue[16]
    for led in indicator_leds:
        led.current = 10mA +/- 10%
    """
    Example LED load represented as resistors
    In real application, these would be LEDs
    """
    # --- Connections ---
    # Power
    led_driver.power ~ power_5v

    # Serial Communication
    led_driver.sdi ~ serial_data_input
    led_driver.dclk ~ data_clock

    # Control signals
    led_driver.le ~ latch_enable
    led_driver.gclk ~ global_clock

    # LED connections
    power_5v.hv ~> indicator_leds[0] ~> led_driver.led_outputs[0].line
    power_5v.hv ~> indicator_leds[1] ~> led_driver.led_outputs[1].line
    power_5v.hv ~> indicator_leds[2] ~> led_driver.led_outputs[2].line
    power_5v.hv ~> indicator_leds[3] ~> led_driver.led_outputs[3].line
    power_5v.hv ~> indicator_leds[4] ~> led_driver.led_outputs[4].line
    power_5v.hv ~> indicator_leds[5] ~> led_driver.led_outputs[5].line
    power_5v.hv ~> indicator_leds[6] ~> led_driver.led_outputs[6].line
    power_5v.hv ~> indicator_leds[7] ~> led_driver.led_outputs[7].line
    power_5v.hv ~> indicator_leds[8] ~> led_driver.led_outputs[8].line
    power_5v.hv ~> indicator_leds[9] ~> led_driver.led_outputs[9].line
    power_5v.hv ~> indicator_leds[10] ~> led_driver.led_outputs[10].line
    power_5v.hv ~> indicator_leds[11] ~> led_driver.led_outputs[11].line
    power_5v.hv ~> indicator_leds[12] ~> led_driver.led_outputs[12].line
    power_5v.hv ~> indicator_leds[13] ~> led_driver.led_outputs[13].line
    power_5v.hv ~> indicator_leds[14] ~> led_driver.led_outputs[14].line
    power_5v.hv ~> indicator_leds[15] ~> led_driver.led_outputs[15].line

```

## Power Requirements

The MBI5043GP-A requires a single 5V power supply:

- **power**: 4.5V to 5.5V - Powers all internal logic and output drivers
- Built-in bypass capacitor for supply decoupling
- Typical supply current: 3-10mA depending on configuration

## Current Setting

Output current is set globally for all channels using an external resistor connected to the REXT pin:

- **744Ω**: ~25mA per channel (recommended for standard LEDs)
- **372Ω**: ~50mA per channel (for higher brightness)
- **186Ω**: ~100mA per channel (maximum current)

The formula is: **I_OUT = 1.253V / R_EXT × 15**

## Interface Signals

- **spi**: Serial data interface (SDI/MOSI, SDO/MISO, DCLK/SCLK)
- **le**: Latch Enable - transfers shift register data to output latches
- **oe**: Output Enable (active low) - global enable/disable for all outputs
- **gclk**: Global Clock - provides PWM timing for brightness control
- **led_outputs[16]**: 16 constant current sink outputs for LEDs

## Thermal Considerations

- Maximum junction temperature: 150°C
- Package power dissipation depends on output current and duty cycle
- For continuous operation at high currents, ensure adequate thermal management
- Consider PCB copper area and ambient temperature in thermal design

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
