# OPSCO SK6805-SIDE Side-Emitting Addressable RGB LED

The SK6805-SIDE is a side-emitting addressable RGB LED with integrated controller, specifically designed for edge lighting and indirect illumination applications. Compatible with the WS2812 protocol, it features a unique side-emission design perfect for creating light guides and edge-lit effects.

## Key Features

- **Side-emitting design**: Light emission from the side for edge lighting applications
- **Compact profile**: 3.5mm × 1.6mm × 0.8mm package optimized for edge mounting
- **Integrated controller**: Built-in IC for signal processing and PWM control
- **WS2812 compatible**: Standard addressable LED protocol
- **24-bit color**: 8 bits per channel (16.7 million colors)
- **Cascading capability**: Chain multiple LEDs with single data line
- **High efficiency**: Optimized light coupling for edge applications
- **Fast switching**: 400Hz PWM frequency, 800Kbps data rate
- **Wide temperature range**: -25°C to +80°C operation

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic

from "opsco-sk6805-side.ato" import OPSCO_SK6805_SIDE

module Usage:
    """
    Minimal usage example for opsco-sk6805-side.

    This example demonstrates chaining 8 side-emitting LEDs
    for edge lighting applications like light guides or indirect illumination.
    """

    # Create array of 8 side-emitting LEDs
    edge_leds = new OPSCO_SK6805_SIDE[8]

    # Power supply (5V for LED strip)
    power_5v = new ElectricPower
    power_5v.voltage = 5.0V +/- 2%

    # Connect power to all LEDs
    for led in edge_leds:
        power_5v ~ led.power

    # Data input from microcontroller
    data_input = new ElectricLogic
    data_input.reference ~ power_5v

    # Chain LEDs together for edge lighting effect
    data_input ~> edge_leds[0] ~> edge_leds[1] ~> edge_leds[2] ~> edge_leds[3] ~> edge_leds[4] ~> edge_leds[5] ~> edge_leds[6] ~> edge_leds[7]
```

## Technical Specifications

### Electrical Characteristics
- **Supply voltage**: 5V ±0.5V (4.5V - 5.5V)
- **Forward current**: 60mA maximum (20mA per color @ full brightness)
- **Power consumption**: ~300mW at full white
- **Input logic high**: >0.7 × VDD
- **Input logic low**: <0.3 × VDD

### Optical Characteristics
- **Emission type**: Side-emitting (90° to PCB surface)
- **Luminous intensity**:
  - Red: 350-380mcd
  - Green: 600-650mcd
  - Blue: 160-180mcd
- **Beam angle**: 120° typical (along emission direction)
- **Color temperature**: Adjustable via RGB mixing
- **PWM resolution**: 8 bits per channel (256 levels)

### Timing Characteristics
- **Data transfer rate**: 800Kbps ±150Kbps
- **PWM frequency**: 400Hz typical
- **Reset time**: >280μs
- **Bit timing**: Compatible with WS2812 standard

## Protocol Details

### WS2812 Protocol Compatibility
The SK6805-SIDE uses the standard WS2812 protocol:
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

- **Package**: LED-SMD 4P, 3.5mm × 1.6mm × 0.8mm
- **Emission direction**: Side-emitting (perpendicular to mounting surface)
- **Mounting**: Surface mount, optimized for edge placement
- **Operating temperature**: -25°C to +80°C
- **Storage temperature**: -40°C to +100°C

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | VDD | Power supply positive (5V) |
| 2 | VSS | Ground |
| 3 | DIN | Data input |
| 4 | DOUT | Data output (to next LED) |

## Applications

### Edge Lighting Applications
- **Acrylic light guides**: Illuminating transparent or translucent panels
- **Display backlighting**: Edge lighting for LCD panels and signage
- **Architectural lighting**: Cove lighting, under-cabinet illumination
- **Automotive**: Dashboard edge lighting, door handle illumination
- **Gaming keyboards**: Per-key edge lighting effects

### Indirect Lighting Applications
- **Ambient lighting**: Bias lighting behind monitors and TVs
- **Furniture lighting**: Table edges, shelf illumination
- **Art installations**: Creating floating light effects
- **Photography**: Edge lighting for product photography
- **Retail displays**: Accent lighting for products and shelving

### Specialized Applications
- **Light boxes**: Creating uniform edge-lit displays
- **Fiber optic coupling**: Feeding light into optical fibers
- **Channel letters**: Illuminating signage from the edges
- **Glass etching**: Highlighting etched glass patterns
- **Strip lighting**: Thin profile LED strips for tight spaces

## Design Considerations

### Optical Design
- **Light coupling**: Consider reflective surfaces to maximize efficiency
- **Light guides**: Use appropriate materials (acrylic, polycarbonate)
- **Beam shaping**: Add diffusers or lenses as needed for uniform illumination
- **Viewing angle**: Orient LEDs for optimal light direction

### Mechanical Layout
- **Edge placement**: Position LEDs close to the edge of light guides
- **Spacing**: Consider LED spacing for uniform illumination
- **Thermal management**: Ensure adequate heat dissipation
- **Protection**: Consider protective covering for exposed LEDs

### Electrical Design
- **Power distribution**: Use adequate power supply and distribution
- **Signal integrity**: Maintain clean data signals for reliable operation
- **Grounding**: Proper ground planes for EMI reduction
- **Decoupling**: Add local decoupling capacitors for each LED

## Control Libraries

Compatible with popular LED control libraries:
- **Arduino**: FastLED, Adafruit NeoPixel
- **Python**: rpi_ws281x, adafruit-circuitpython-neopixel
- **ESP32/ESP8266**: FastLED, NeoPixelBus
- **Raspberry Pi**: ws2812, pigpio

## Light Guide Design Tips

### Material Selection
- **Acrylic (PMMA)**: Excellent light transmission, easy to machine
- **Polycarbonate**: Higher impact resistance, good transmission
- **Glass**: Best optical quality, higher cost

### Edge Preparation
- **Polished edges**: Critical for efficient light coupling
- **Perpendicular surfaces**: Ensure LED alignment with guide edge
- **Protective film**: Remove before installation to avoid losses

### Diffusion Techniques
- **Etched patterns**: Create uniform light extraction
- **Printed dots**: Control light distribution along the guide
- **Textured surfaces**: Add diffusion for softer lighting effects

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
