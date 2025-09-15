# Worldsemi WS2812B Ultra-Compact Addressable RGB LED

The WS2812B is an ultra-compact addressable RGB LED that integrates control circuit and RGB chip in a tiny 2020 package (2.0mm × 2.0mm). It provides the same powerful features as larger WS2812 variants while occupying only 1/8th the space, making it perfect for high-density applications, wearables, and space-constrained designs.

## Key Features

- **Ultra-compact size**: 2.0mm × 2.0mm × 0.84mm (2020 package)
- **Space efficiency**: Only 1/8 the size of traditional 5050 LEDs
- **Integrated controller**: Built-in WS2812B control IC with RGB LED
- **Single-wire protocol**: Simple serial communication (800kHz)
- **24-bit color depth**: 8-bit resolution per color channel (16.7M colors)
- **Wide supply voltage**: 3.5V to 5.3V (improved range)
- **Ultra-low power**: ~20mA maximum per LED (reduced from 60mA)
- **High-density capable**: Perfect for LED matrices and strips
- **Latest MOLDING technology**: Enhanced heat dissipation and reliability
- **Temperature range**: -20°C to +60°C operating

## Usage

```ato
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
import ElectricLogic

from "atopile/worldsemi-ws2812b/worldsemi-ws2812b.ato" import Worldsemi_WS2812B_2020
from "atopile/worldsemi-ws2812b/worldsemi-ws2812b.ato" import Worldsemi_WS2812B_4020
from "atopile/worldsemi-ws2812b/worldsemi-ws2812b.ato" import Worldsemi_WS2812B_5050
from "atopile/worldsemi-ws2812b/worldsemi-ws2812b.ato" import WS2812B_2020_HighDensity_Strip
from "atopile/worldsemi-ws2812b/worldsemi-ws2812b.ato" import WS2812B_2020_Matrix

module Usage:
    """
    Usage examples for Worldsemi WS2812B-2020 ultra-compact addressable RGB LEDs.

    This example demonstrates:
    - Single compact LED configuration
    - High-density LED strip (5 LEDs)
    - 5×5 LED matrix for displays
    - Wearable electronics applications
    - Power management for compact designs
    """

    # --- Single LED Example ---
    led_2020 = new Worldsemi_WS2812B_2020
    led_4020 = new Worldsemi_WS2812B_4020
    led_5050 = new Worldsemi_WS2812B_5050

    # Power supply for compact LED (5V or 3.3V)
    power_5v = new ElectricPower
    power_5v.voltage = 5V +/- 5%
    power_5v ~ led_2020.power
    power_5v ~ led_4020.power
    power_5v ~ led_5050.power

    # Data input from microcontroller
    mcu_data = new ElectricLogic
    """Data signal from microcontroller GPIO"""
    mcu_data ~> led_2020 ~> led_4020 ~> led_5050.data_in
    power_5v ~ mcu_data.reference

    # --- High-Density Strip Example ---
    hd_strip = new WS2812B_2020_HighDensity_Strip

    # Connect power supply to high-density strip
    power_5v ~ hd_strip.power

    # Separate data line for strip
    strip_data = new ElectricLogic
    """Data signal for high-density LED strip"""
    strip_data ~ hd_strip.data_in
    power_5v ~ strip_data.reference

    # --- 5×5 Matrix Example ---
    led_matrix = new WS2812B_2020_Matrix

    # Connect power to matrix
    power_5v ~ led_matrix.power

    # Matrix data control
    matrix_data = new ElectricLogic
    """Data signal for 5×5 LED matrix"""
    matrix_data ~ led_matrix.data_in
    power_5v ~ matrix_data.reference

```

## Technical Specifications

### Physical Characteristics
- **Package**: 2020 SMD (2.0mm × 2.0mm × 0.84mm)
- **Weight**: Ultra-lightweight design
- **Pin count**: 4 pins (VCC, GND, DIN, DOUT)
- **Mounting**: Surface mount technology (SMT)
- **Assembly difficulty**: High (requires precision placement)

### Electrical Characteristics
- **Supply Voltage**: 3.5V - 5.3V DC (improved range)
- **Current Consumption**:
  - Per LED maximum: ~20mA (full white)
  - Per color channel: ~7mA maximum
  - Low power mode: 5mA
  - Standby current: <1mA
- **Logic Levels**: Compatible with 3.3V and 5V microcontrollers
- **Reverse polarity protection**: Built-in protection circuitry

### Optical Characteristics
- **Color Format**: 24-bit RGB (GRB data order)
- **PWM Resolution**: 8-bit per channel (256 levels each)
- **PWM Frequency**: ~400Hz for color control
- **Luminous Intensity**:
  - Red: 300-500 mcd
  - Green: 800-1500 mcd
  - Blue: 200-300 mcd
- **Beam Angle**: 120° typical
- **Wavelengths**:
  - Red: 620-630nm
  - Green: 515-525nm
  - Blue: 465-475nm

### Communication Protocol
- **Data Rate**: 800 kHz
- **Pulse Width**: 1.25μs
- **Data Format**: Single NZR (Non-Return-to-Zero) communication
- **Chain Length**: Supports 1024+ pixels at 30fps
- **Signal transmission**: Up to 3m between pixels

### Timing Characteristics
- **T0H (0-bit high)**: 0.35μs ±150ns
- **T0L (0-bit low)**: 0.8μs ±150ns
- **T1H (1-bit high)**: 0.7μs ±150ns
- **T1L (1-bit low)**: 0.6μs ±150ns
- **Reset Time**: >50μs (>300μs for newer versions)

## Circuit Design Notes

### PCB Layout for 2020 Package
- **Pad size**: ~2mm × 1mm recommended
- **Thermal management**: Adequate copper pour for heat dissipation
- **Component spacing**: Tight spacing possible due to small size
- **Via placement**: Keep vias away from LED optical area
- **Ground plane**: Solid ground reference essential

### Power Supply Design
- **Bulk Capacitance**: 220μF per 20-30 LEDs for power smoothing
- **Local Decoupling**: 100nF ceramic capacitor per LED (critical)
- **High-frequency filtering**: Additional 10μF for 2020 LEDs
- **Voltage regulation**: Stable 5V or 3.3V supply
- **Current calculation**: Plan for 20mA per LED maximum

### Data Signal Integrity
- **Series resistor**: 330Ω on data input for protection
- **Signal routing**: Keep traces short and controlled impedance
- **Level shifting**: May be needed for 3.3V microcontroller interfacing
- **EMI considerations**: Proper grounding and filtering

### Assembly Considerations
- **Moisture sensitivity**: MSL 5a level - requires special handling
- **Soldering**: Fine-tip iron and precision placement required
- **Inspection**: Optical inspection recommended due to small size
- **Testing**: Individual LED testing before assembly into strips

## Programming Examples

### Arduino/ESP32 with FastLED
```cpp
#include <FastLED.h>

#define LED_PIN     2
#define NUM_LEDS    20        // High-density strip
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  128       // Reduced for lower power

CRGB leds[NUM_LEDS];

void setup() {
    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);
}

void loop() {
    // High-resolution rainbow for compact display
    for(int i = 0; i < NUM_LEDS; i++) {
        leds[i] = CHSV(i * (255/NUM_LEDS), 255, 255);
    }
    FastLED.show();
    delay(50);
}
```

### MicroPython for Wearables
```python
import neopixel
from machine import Pin
import time

# Initialize compact NeoPixel array
np = neopixel.NeoPixel(Pin(2), 8)  # 8 LEDs for wearable

# Breathing effect for wearables
def breathing_effect():
    for brightness in range(0, 128, 2):
        for i in range(8):
            np[i] = (brightness, brightness//2, brightness//4)
        np.write()
        time.sleep_ms(20)
```

## Applications

### High-Density Applications
- **LED matrices**: High-resolution displays and signs
- **Pixel art displays**: Retro gaming and art installations
- **Status indicators**: Dense arrays of status lights
- **Backlighting**: LCD/OLED display backlighting

### Wearable Electronics
- **Smart clothing**: Interactive fashion and cosplay
- **Jewelry**: LED jewelry and accessories
- **Fitness wearables**: Activity indicators and notifications
- **Safety gear**: High-visibility clothing and equipment

### Space-Constrained Designs
- **IoT devices**: Compact smart home devices
- **Portable electronics**: Battery-powered LED devices
- **Model lighting**: Scale models and dioramas
- **Automotive**: Interior accent lighting

### Professional Applications
- **Stage lighting**: High-density lighting arrays
- **Photography**: Compact LED panels for photography
- **Medical devices**: Indicator lights in compact medical equipment
- **Aerospace**: Weight and space-critical applications

## Size Comparison

| Package | Dimensions (mm) | Area (mm²) | Relative Size |
|---------|----------------|------------|---------------|
| WS2812B-2020 | 2.0 × 2.0 × 0.84 | 4.0 | 1× (Reference) |
| WS2812C-5050 | 5.0 × 5.0 × 1.6 | 25.0 | 6.25× larger |
| Traditional LED | 3.0 × 1.4 × 1.2 | 4.2 | Similar |

## Advantages over 5050 Package
- **Space efficiency**: 6.25× more compact than 5050
- **Lower power consumption**: ~20mA vs ~60mA
- **Higher density**: More LEDs per unit area
- **Weight reduction**: Significant for wearable applications
- **Cost effectiveness**: Lower material usage
- **Design flexibility**: Enables new form factors

## Package Information
- **Part Number**: C965555 (JLCPCB)
- **Manufacturer**: Worldsemi
- **Package Type**: 2020 SMD
- **RoHS**: Compliant
- **Moisture Sensitivity**: MSL 5a
- **Operating Temperature**: -20°C to +60°C
- **Storage Temperature**: -40°C to +80°C

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
