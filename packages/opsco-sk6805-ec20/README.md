# OPSCO SK6805-EC20 Addressable RGB LED

The SK6805-EC20 is a compact 2x2mm addressable RGB LED with integrated controller, compatible with the popular WS2812 protocol. Each LED contains red, green, and blue chips with independent PWM control and a built-in IC for signal processing.

## Key Features

- **Compact size**: 2.0mm × 2.0mm × 0.8mm package
- **Integrated controller**: Built-in IC for signal processing and PWM control
- **WS2812 compatible**: Standard addressable LED protocol
- **24-bit color**: 8 bits per channel (16.7 million colors)
- **Cascading capability**: Chain multiple LEDs with single data line
- **High brightness**: Optimized for vivid color reproduction
- **Fast switching**: 400Hz PWM frequency, 800Kbps data rate
- **Wide temperature range**: -25°C to +80°C operation

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic

from "opsco-sk6805-ec20.ato" import OPSCO_SK6805_EC20

module Usage:
    """
    Minimal usage example for opsco-sk6805-ec20.

    This example demonstrates chaining 10 addressable RGB LEDs
    to create a simple LED strip for colorful lighting effects.
    """

    # Create array of 10 LEDs
    leds = new OPSCO_SK6805_EC20[10]

    # Power supply (5V for LED strip)
    power_5v = new ElectricPower
    power_5v.voltage = 5.0V +/- 2%

    # Connect power to all LEDs
    for led in leds:
        power_5v ~ led.power

    # Data input from microcontroller
    data_input = new ElectricLogic
    data_input.reference ~ power_5v

    # Chain LEDs together: data flows through each LED
    data_input ~> leds[0] ~> leds[1] ~> leds[2] ~> leds[3] ~> leds[4] ~> leds[5] ~> leds[6] ~> leds[7] ~> leds[8] ~> leds[9]
```

## Technical Specifications

### Electrical Characteristics
- **Supply voltage**: 5V ±0.5V (4.5V - 5.5V)
- **Forward current**: 60mA maximum (20mA per color @ full brightness)
- **Power consumption**: ~300mW at full white
- **Input logic high**: >0.7 × VDD
- **Input logic low**: <0.3 × VDD

### Optical Characteristics
- **Luminous intensity**:
  - Red: 390-420mcd
  - Green: 660-720mcd
  - Blue: 180-200mcd
- **Viewing angle**: 120° typical
- **Color temperature**: Adjustable via RGB mixing
- **PWM resolution**: 8 bits per channel (256 levels)

### Timing Characteristics
- **Data transfer rate**: 800Kbps ±150Kbps
- **PWM frequency**: 400Hz typical
- **Reset time**: >280μs
- **Bit timing**: Compatible with WS2812 standard

## Protocol Details

### WS2812 Protocol Compatibility
The SK6805-EC20 uses the standard WS2812 protocol:
- **Logic 1**: 850ns ±150ns high, 400ns ±150ns low
- **Logic 0**: 400ns ±150ns high, 850ns ±150ns low
- **Reset**: >280μs low signal

### Data Format
Each LED requires 24 bits of data:
- **Bits 23-16**: Green channel (G7-G0)
- **Bits 15-8**: Red channel (R7-R0)
- **Bits 7-0**: Blue channel (B7-B0)
- **Data order**: GRB (Green-Red-Blue)

## Package Information

- **Package**: LED-SMD 4P, 2.0mm × 2.0mm × 0.8mm
- **Pin pitch**: 2.0mm × 1.6mm pad spacing
- **Mounting**: Surface mount, reflow compatible
- **Operating temperature**: -25°C to +80°C
- **Storage temperature**: -40°C to +100°C

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | VDD | Power supply positive (5V) |
| 2 | DOUT | Data output (to next LED) |
| 3 | GND | Ground |
| 4 | DIN | Data input |

## Applications

- **LED strips and matrices**: Decorative and functional lighting
- **Wearable electronics**: Clothing, accessories, costumes
- **Gaming peripherals**: RGB keyboards, mice, headsets
- **Architectural lighting**: Accent lighting, color-changing installations
- **Signage and displays**: Dynamic color displays and indicators
- **Art installations**: Interactive and kinetic light sculptures
- **Holiday decorations**: RGB Christmas lights, party decorations
- **IoT indicators**: Status lights for smart devices
- **Automotive**: Interior accent lighting, underglow kits

## Control Libraries

Compatible with popular LED control libraries:
- **Arduino**: FastLED, Adafruit NeoPixel
- **Python**: rpi_ws281x, adafruit-circuitpython-neopixel
- **ESP32/ESP8266**: FastLED, NeoPixelBus
- **Raspberry Pi**: ws2812, pigpio

## Design Considerations

### Power Supply
- Use adequate power supply: ~60mA per LED at full brightness
- Add bulk capacitance: 1000μF per 30-50 LEDs
- Consider voltage drop: Use appropriate wire gauge for long strips

### Signal Integrity
- Keep data lines short and use proper impedance matching
- Add level shifters for 3.3V microcontrollers
- Consider signal regeneration for long chains (>100 LEDs)

### Thermal Management
- Ensure adequate airflow for high-density installations
- Consider thermal pads or heat sinks for continuous operation
- Limit brightness for enclosed applications

### EMI Considerations
- Add ferrite beads on power and data lines if needed
- Use twisted pair for data signals in noisy environments
- Proper ground plane design for PCB layouts

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
