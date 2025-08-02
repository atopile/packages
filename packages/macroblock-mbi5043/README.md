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
import ElectricPower, Resistor, ElectricLogic, SPI

from "macroblock-mbi5043.ato" import Macroblock_MBI5043

module Usage:
    """
    Minimal usage example for macroblock-mbi5043.
    Demonstrates basic LED driver configuration with SPI control.
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
    spi_controller = new SPI
    """
    SPI interface from microcontroller to LED driver
    """

    latch_enable = new ElectricLogic
    """
    Latch enable signal - controlled by microcontroller GPIO
    """
    latch_enable.reference ~ power_5v

    output_enable = new ElectricLogic
    """
    Output enable signal - controlled by microcontroller GPIO
    """
    output_enable.reference ~ power_5v

    global_clock = new ElectricLogic
    """
    Global clock for PWM - controlled by microcontroller PWM output
    """
    global_clock.reference ~ power_5v

    # --- LED Load Examples ---
    led_array = new Resistor[16]
    """
    Example LED load represented as resistors
    In real application, these would be LEDs
    """
    for led in led_array:
        led.resistance = 100ohm +/- 5%  # Typical LED + current limiting resistor equivalent
        led.package = "0603"

    # --- Connections ---
    # Power
    led_driver.power ~ power_5v

    # SPI Communication
    led_driver.spi ~ spi_controller

    # Control signals
    led_driver.le ~ latch_enable
    led_driver.oe ~ output_enable
    led_driver.gclk ~ global_clock

    # LED connections
    for i in range(16):
        power_5v.hv ~> led_array[i] ~> led_driver.led_outputs[i].line
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
