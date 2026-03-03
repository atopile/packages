# OPSCO SK6805-EC15 Ultra-Compact Addressable RGB LED

The SK6805-EC15 is the smallest member of the SK6805 addressable LED family, featuring an ultra-compact 0606 package (1.5mm × 1.5mm) while maintaining full WS2812 compatibility. Perfect for high-density LED applications where space is extremely limited.

## Key Features

- **Ultra-compact size**: 1.5mm × 1.5mm × 0.8mm (0606 package)
- **Highest density**: Smallest addressable RGB LED in the SK6805 family
- **WS2812 compatible**: Standard addressable LED protocol
- **24-bit color**: 8 bits per channel (16.7 million colors)
- **Cascading capability**: Chain multiple LEDs with single data line
- **High efficiency**: Optimized for maximum brightness in minimal space
- **Fast switching**: 400Hz PWM frequency, 800Kbps data rate
- **Wide temperature range**: -40°C to +80°C operation
- **Precise wavelengths**: R(620-625nm), G(520-530nm), B(460-470nm)

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import ElectricLogic

from "atopile/opsco-sk6805-ec15/opsco-sk6805-ec15.ato" import OPSCO_SK6805_EC15

module Usage:
    """
    Minimal usage example for opsco-sk6805-ec15.

    This example demonstrates a high-density LED matrix using the ultra-compact
    0606 SK6805-EC15 LEDs for applications requiring maximum LED density.
    """

    # Create 4×4 matrix of ultra-compact LEDs (16 total)
    led_matrix = new OPSCO_SK6805_EC15[16]

    # Power supply (5V for LED matrix)
    power_5v = new ElectricPower
    power_5v.voltage = 5.0V +/- 2%

    # Connect power to all LEDs
    for led in led_matrix:
        power_5v ~ led.power

    # Data input from microcontroller
    data_input = new ElectricLogic
    data_input.reference ~ power_5v

    # Chain LEDs in matrix order for high-density display
    data_input ~> led_matrix[0] ~> led_matrix[1] ~> led_matrix[2] ~> led_matrix[3] ~> led_matrix[4] ~> led_matrix[5] ~> led_matrix[6] ~> led_matrix[7] ~> led_matrix[8] ~> led_matrix[9] ~> led_matrix[10] ~> led_matrix[11] ~> led_matrix[12] ~> led_matrix[13] ~> led_matrix[14] ~> led_matrix[15]

```

## Technical Specifications

### Physical Characteristics
- **Package**: 0606 (1.5mm × 1.5mm × 0.8mm)
- **Weight**: Ultra-lightweight for minimal PCB impact
- **Pin pitch**: 0.8mm (optimized for high-density layouts)
- **Mounting**: Surface mount, fine-pitch assembly required

### Electrical Characteristics
- **Supply voltage**: 5V ±0.5V (4.5V - 5.5V)
- **Forward current**: 60mA maximum (20mA per color @ full brightness)
- **Power consumption**: ~300mW at full white
- **Input logic high**: >0.7 × VDD
- **Input logic low**: <0.3 × VDD

### Optical Characteristics
- **Luminous intensity**: Optimized for small package
  - Red: 280-320mcd (620-625nm)
  - Green: 560-600mcd (520-530nm)
  - Blue: 140-160mcd (460-470nm)
- **Viewing angle**: 120° typical
- **Color accuracy**: High-precision wavelength control
- **PWM resolution**: 8 bits per channel (256 levels)

### Timing Characteristics
- **Data transfer rate**: 800Kbps ±150Kbps
- **PWM frequency**: 400Hz typical
- **Reset time**: >280μs
- **Bit timing**: Compatible with WS2812 standard

## Size Comparison

| Model | Package | Dimensions | Density | Application |
|-------|---------|------------|---------|-------------|
| SK6805-EC15 | 0606 | 1.5×1.5mm | Highest | Micro displays, wearables |
| SK6805-EC20 | 2020 | 2.0×2.0mm | High | LED strips, general use |
| SK6805-SIDE | 3516 | 3.5×1.6mm | Medium | Edge lighting |

## Protocol Details

### WS2812 Protocol Compatibility
The SK6805-EC15 uses the standard WS2812 protocol:
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

- **LCSC Part Number**: C2890035
- **Package**: 0606 (1.5mm × 1.5mm × 0.8mm)
- **Operating Temperature**: -40°C to +80°C
- **Storage Temperature**: -40°C to +100°C
- **Manufacturer**: OPSCO Optoelectronics
- **Part Number**: SK6805-EC15
- **MSL Level**: 4 (72 hours @ 30°C/60% RH)

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | VDD | Power supply positive (5V) |
| 2 | DOUT | Data output (to next LED) |
| 3 | GND | Ground |
| 4 | DIN | Data input |

## Applications

### High-Density Applications
- **Micro LED displays**: Ultra-fine pitch LED matrices
- **Wearable electronics**: Smart watches, fitness trackers, jewelry
- **Miniature indicators**: Status lights for compact devices
- **PCB art**: Fine-detail light patterns and designs
- **Medical devices**: Compact diagnostic equipment indicators

### Space-Constrained Applications
- **IoT sensors**: Ultra-compact status indicators
- **Drone racing**: Lightweight racing drone lighting
- **Model lighting**: RC cars, planes, boats
- **Embedded systems**: Compact development boards
- **Portable devices**: Battery-powered gadgets

### Professional Applications
- **Camera equipment**: Focus assist lights, status indicators
- **Test equipment**: High-density status arrays
- **Scientific instruments**: Precision indication systems
- **Automotive**: Dashboard micro-indicators
- **Aerospace**: Space-constrained avionics lighting

## Design Considerations

### High-Density Layout
- **Thermal management**: Consider heat dissipation in dense arrays
- **Power distribution**: Use adequate power planes and distribution
- **Signal integrity**: Maintain clean data signals for reliable operation
- **Assembly**: Requires precision SMT equipment and processes

### PCB Design Guidelines
- **Pad design**: Follow manufacturer recommendations for 0606 packages
- **Via placement**: Avoid vias under LED packages
- **Ground planes**: Continuous ground plane for thermal and electrical performance
- **Trace width**: Adequate current-carrying capacity for power traces

### Power Supply Design
- **Bulk capacitance**: 1000μF per 50-100 micro LEDs
- **Local decoupling**: Consider 0201 capacitors for space efficiency
- **Voltage regulation**: Tight regulation required for consistent brightness
- **Current calculation**: ~20mA per LED at full brightness

### Assembly Considerations
- **Reflow profile**: MSL 4 requires careful moisture handling
- **Pick and place**: High-precision equipment required for 0606 placement
- **Inspection**: AOI systems for quality verification
- **Rework**: Challenging due to small size, prevention is key

## Software Libraries

Compatible with standard WS2812 libraries:
- **Arduino**: FastLED, Adafruit NeoPixel
- **Python**: rpi_ws281x, adafruit-circuitpython-neopixel
- **ESP32/ESP8266**: FastLED, NeoPixelBus
- **Raspberry Pi**: ws2812, pigpio

## Performance Optimization

### For High LED Counts
- **Power staging**: Distribute power to avoid voltage drops
- **Signal regeneration**: Consider buffers for long chains
- **Timing precision**: Ensure stable data signals
- **Thermal design**: Heat sinks or thermal vias for dense arrays

### For Battery Applications
- **Brightness limiting**: Reduce current for longer battery life
- **Dynamic brightness**: Adjust based on ambient light
- **Sleep modes**: Turn off unused LEDs to save power
- **Efficient protocols**: Minimize update frequency

## Comparison with Larger Variants

### Advantages of EC15
- **Highest density**: Maximum LEDs per unit area
- **Lowest profile**: Minimal z-height impact
- **Precise control**: Individual pixel control in tiny space
- **Weight savings**: Important for battery/portable applications

### When to Use Larger Variants
- **Easier assembly**: EC20 more forgiving for hand soldering
- **Higher brightness**: Larger packages can handle more current
- **Cost optimization**: Larger variants may be more cost-effective
- **Thermal management**: Larger packages dissipate heat better

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
