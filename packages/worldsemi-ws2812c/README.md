# Worldsemi WS2812C Addressable RGB LED

The WS2812C is an intelligent control LED integrated light source that incorporates a control circuit and RGB chip in a 5050 component package. It features single-wire serial communication, 24-bit color depth, and cascadable design for creating LED strips and matrices.

## Key Features

- **Integrated controller**: Built-in WS2812C control IC with RGB LED
- **Single-wire protocol**: Simple serial communication with precise timing
- **24-bit color depth**: 8-bit resolution per color channel (16.7M colors)
- **Wide supply voltage**: 3.7V to 5.3V (5V recommended)
- **Low power standby**: <1mA when idle
- **High PWM frequency**: 2kHz for smooth operation and reduced flicker
- **Cascadable design**: Unlimited chaining capability
- **SMD5050 package**: 5mm × 5mm × 1.6mm surface mount
- **Temperature range**: -25°C to +85°C operating

## Usage

```ato
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("TRAITS")

import ElectricPower
import ElectricLogic

from "atopile/worldsemi-ws2812c/worldsemi-ws2812c.ato" import Worldsemi_WS2812C_2020
from "atopile/worldsemi-ws2812c/worldsemi-ws2812c.ato" import Worldsemi_WS2812C_4020
from "atopile/worldsemi-ws2812c/worldsemi-ws2812c.ato" import Worldsemi_WS2812C_5050
from "atopile/worldsemi-ws2812c/worldsemi-ws2812c.ato" import WS2812C_5050_Strip
from "atopile/worldsemi-ws2812c/worldsemi-ws2812c.ato" import WS2812C_5050_Matrix

module Usage:
    """
    Usage examples for Worldsemi WS2812C addressable RGB LEDs.

    This example demonstrates:
    - Single LED configuration
    - LED strip with multiple LEDs
    - Proper power supply and data connections
    - Matrix example
    """

    # --- Single LED Example ---
    led_2020 = new Worldsemi_WS2812C_2020
    led_4020 = new Worldsemi_WS2812C_4020
    led_5050 = new Worldsemi_WS2812C_5050

    # Power supply for single LED (5V)
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

    # --- LED Strip Example ---
    led_strip = new WS2812C_5050_Strip

    # Connect same power supply to strip
    power_5v ~ led_strip.power

    # Separate data line for strip
    strip_data = new ElectricLogic
    """Data signal for LED strip"""
    strip_data ~ led_strip.data_in

    # Matrix
    led_matrix = new WS2812C_5050_Matrix

    # Connect power to matrix
    power_5v ~ led_matrix.power

```

## Technical Specifications

### Electrical Characteristics
- **Supply Voltage**: 3.7V - 5.3V DC (5V recommended)
- **Current Consumption**:
  - Maximum per LED: 60mA (full white)
  - Per color channel: 20mA maximum
  - Standby current: <1mA
- **Logic Levels**: Compatible with 3.3V and 5V microcontrollers

### Optical Characteristics
- **Color Format**: 24-bit RGB (GRB data order)
- **PWM Resolution**: 8-bit per channel (256 levels each)
- **PWM Frequency**: 2kHz (improved from earlier versions)
- **Luminous Intensity**: High brightness RGB output
- **Viewing Angle**: 120° typical

### Communication Protocol
- **Data Rate**: 800 kbps (800kHz)
- **Data Format**: Serial, single-wire communication
- **Bit Order**: MSB first, GRB color order
- **Reset Time**: ≥300µs low signal to latch data
- **Chain Length**: Theoretically unlimited (practical limits apply)

### Timing Characteristics
- **T0H (0-bit high)**: 0.35µs ±0.15µs
- **T0L (0-bit low)**: 0.8µs ±0.15µs
- **T1H (1-bit high)**: 0.7µs ±0.15µs
- **T1L (1-bit low)**: 0.6µs ±0.15µs
- **RES (reset)**: >50µs low signal

## Circuit Design Notes

### Power Supply Design
- **Bulk Capacitance**: 100µF per 10-20 LEDs for power smoothing (integrated in strip driver)
- **Local Decoupling**: 100nF ceramic capacitor per LED (integrated in driver)
- **Voltage Regulation**: Stable 5V supply recommended
- **Current Calculation**: Plan for 60mA per LED maximum

### Data Signal Integrity
- **Series Resistor**: 330Ω on data input for signal protection (integrated in driver)
- **Signal Routing**: Keep data traces short and away from power switching
- **Ground Plane**: Solid ground reference for stable operation
- **Level Shifting**: Use level shifter for 3.3V microcontroller interfacing

### PCB Layout Guidelines
- **Thermal Management**: Adequate copper pour for heat dissipation
- **Power Distribution**: Wide traces for power and ground
- **Component Placement**: Keep decoupling capacitors close to LED power pins
- **Via Stitching**: Connect ground layers with multiple vias

## Programming Examples

### Arduino/ESP32
```cpp
#include <FastLED.h>

#define LED_PIN     2
#define NUM_LEDS    10
#define LED_TYPE    WS2812
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

void setup() {
    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(50);
}

void loop() {
    // Rainbow effect
    for(int i = 0; i < NUM_LEDS; i++) {
        leds[i] = CHSV(i * 25, 255, 255);
    }
    FastLED.show();
    delay(100);
}
```

### MicroPython
```python
import neopixel
from machine import Pin

# Initialize NeoPixel strip
np = neopixel.NeoPixel(Pin(2), 10)

# Set colors (R, G, B)
np[0] = (255, 0, 0)    # Red
np[1] = (0, 255, 0)    # Green
np[2] = (0, 0, 255)    # Blue
np.write()
```

## Applications
- LED strips and matrices for displays
- Decorative lighting and mood lighting
- Wearable electronics and cosplay
- Art installations and sculptures
- Computer case lighting and peripherals
- Stage lighting and entertainment
- IoT projects and smart home devices

## WS2812C vs WS2812B Improvements
- **Enhanced PWM frequency**: 2kHz (vs lower frequencies in WS2812B)
- **Improved current transients**: Slower rise/fall times reduce power supply noise
- **Better chain performance**: Reduced signal integrity issues in long chains
- **Lower EMI**: Improved electrical characteristics for cleaner operation

## Package Information
- **Part Number**: C114587 (JLCPCB)
- **Manufacturer**: Worldsemi
- **IC Part Number**: WS2812C
- **Package**: SMD5050 (5.0mm × 5.0mm × 1.6mm)
- **Pins**: 4-pin PLCC configuration
- **Mounting**: Surface mount technology (SMT)
- **RoHS**: Compliant
- **Stock**: Available on JLCPCB

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
