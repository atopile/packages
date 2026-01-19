# Vishay VEML7700 High Accuracy Ambient Light Sensor

The VEML7700 is a high accuracy ambient light digital 16-bit resolution sensor in a miniature transparent package. It includes a high sensitive photodiode, a low noise amplifier, a 16-bit A/D converter and supports an easy to use I²C bus communication interface.

## Key Features

- **16-bit resolution**: Digital ambient light data with high accuracy
- **Wide detection range**: 0 lux to about 120,000 lux with excellent linearity
- **High sensitivity**: 0.0036 lux/count resolution
- **I²C interface**: Simple 2-wire communication (address: 0x10)
- **Low power**: 300 µA typical operating current
- **Fast conversion**: 25ms to 800ms programmable integration time
- **Wide supply range**: 2.5V to 3.6V
- **Operating temperature**: -25°C to +85°C
- **Small package**: SMD-4P (6.8mm × 2.35mm × 3.0mm)
- **Excellent linearity**: Across the entire detection range

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C

from "atopile/vishay-veml7700/vishay-veml7700.ato" import Vishay_VEML7700

module Usage:
    """
    Minimal usage example for vishay-veml7700.

    This example demonstrates basic I²C connection for the VEML7700
    ambient light sensor with automatic lux measurement capability.
    """

    light_sensor = new Vishay_VEML7700

    # External I²C bus
    i2c = new I2C
    i2c ~ light_sensor.i2c

    # Power supply (3.3V typical)
    power_3v3 = new ElectricPower
    power_3v3.voltage = 3.3V +/- 5%

    power_3v3 ~ light_sensor.power

    # Set I²C address (fixed at 0x10)
    assert light_sensor.i2c.address within 0x10

```

## Interface Details

### I²C Communication
- **Address**: 0x10 (7-bit, fixed)
- **Clock speeds**: Standard mode (100 kHz), Fast mode (400 kHz)
- **Data format**: 16-bit ambient light sensor data

### Power Supply
- **VDD**: 2.5V to 3.6V (typical 3.3V)
- **Current consumption**:
  - Active: 300 µA typical
  - Shutdown: 5 µA typical
- **I²C logic levels**: Compatible with 1.7V to 3.6V

## Sensor Characteristics

### Detection Range and Resolution
- **Range**: 0 lux to ~120,000 lux
- **Resolution**: 0.0036 lux/count (at gain ×1, IT = 800ms)
- **Sensitivity**: Optimized for human eye response
- **Linearity**: Excellent across entire range

### Integration Time Settings
- **25ms**: Fast response, lower resolution
- **50ms**: Balanced response and resolution
- **100ms**: Good resolution
- **200ms**: High resolution
- **400ms**: Very high resolution
- **800ms**: Maximum resolution (default)

### Gain Settings
- **×1/8**: For very bright environments (up to ~120,000 lux)
- **×1/4**: For bright environments (up to ~30,000 lux)
- **×1**: Default gain (up to ~7,500 lux)
- **×2**: For low light environments (up to ~3,750 lux)

## Package Information

- **LCSC Part Number**: C1850416
- **Package**: SMD-4P (6.8mm × 2.35mm × 3.0mm)
- **Operating Temperature**: -25°C to +85°C
- **Storage Temperature**: -40°C to +125°C
- **Manufacturer**: Vishay Intertech
- **Part Number**: VEML7700-TT

## Pin Configuration

| Pin | Name | Description |
|-----|------|-------------|
| 1 | SCL | I²C clock input |
| 2 | GND | Ground |
| 3 | SDA | I²C data input/output |
| 4 | VDD | Power supply (2.5V - 3.6V) |

## Applications

- **Display brightness control**: Automatic screen brightness adjustment
- **Smart lighting**: Adaptive lighting systems
- **IoT sensors**: Environmental monitoring systems
- **Mobile devices**: Ambient light sensing for power management
- **Automotive**: Dashboard and interior lighting control
- **Home automation**: Automatic lighting control
- **Industrial**: Light monitoring and control systems
- **Security systems**: Day/night detection
- **Photography equipment**: Light metering applications

## Register Map

The VEML7700 provides several configurable registers:

- **ALS_CONF (00h)**: Configuration register for gain, integration time, etc.
- **ALS_WH (01h)**: ALS high threshold window setting
- **ALS_WL (02h)**: ALS low threshold window setting
- **PWR_SAVING (03h)**: Power saving mode settings
- **ALS (04h)**: ALS measurement data
- **WHITE (05h)**: White channel measurement data
- **ALS_INT (06h)**: ALS interrupt status

## Calculation Examples

### Lux Calculation
```
Resolution = 0.0036 × (800ms/IT) × (GAIN/1)
Lux = ALS_Counts × Resolution
```

### Integration Time vs Resolution
- **800ms, Gain ×1**: 0.0036 lux/count
- **400ms, Gain ×1**: 0.0072 lux/count
- **200ms, Gain ×1**: 0.0144 lux/count
- **100ms, Gain ×1**: 0.0288 lux/count

## Power Management

The VEML7700 supports several power modes:

- **Normal mode**: Continuous measurements
- **Shutdown mode**: <5 µA current consumption
- **Power saving modes**: Reduced measurement frequency for battery applications

## Temperature Compensation

The sensor includes excellent temperature compensation across its operating range, maintaining accuracy from -25°C to +85°C without external calibration.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
