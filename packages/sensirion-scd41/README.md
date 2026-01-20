# Sensirion SCD41 CO2, Temperature, and Humidity Sensor

The Sensirion SCD41 is a high-accuracy CO2 sensor that combines photoacoustic NDIR CO2 sensing with integrated temperature and humidity measurements. It features an extended measurement range of 400-5000 ppm, making it ideal for industrial and scientific applications requiring precise CO2 monitoring.

## Key Features

- **CO2 Measurement**: 400-5000 ppm range with ±(40 ppm + 5% of reading) accuracy
- **Photoacoustic NDIR Technology**: True CO2 sensing using Sensirion's patented PASens® technology
- **Multi-sensor Integration**: Built-in SHT4x temperature and humidity sensor for environmental compensation
- **Low Power Operation**: Single-shot measurement mode for battery-powered applications
- **I2C Interface**: Simple integration with fixed address 0x62
- **Wide Supply Range**: 2.4V to 5.5V operation
- **Compact Package**: LGA-20 package (10.1 x 10.1 mm)
- **Self-Calibration**: Automatic baseline correction eliminates need for manual calibration

## Technical Specifications

### CO2 Sensing
- **Range**: 400-5000 ppm
- **Accuracy**: ±(40 ppm + 5% of reading)
- **Technology**: Photoacoustic NDIR (Non-Dispersive Infrared)
- **Response Time**: < 60 seconds (for 63% of step change)

### Environmental Sensing
- **Temperature**: Built-in SHT4x sensor
- **Humidity**: Built-in SHT4x sensor with on-chip signal compensation

### Electrical Characteristics
- **Supply Voltage**: 2.4V to 5.5V (typically 3.3V)
- **I2C Address**: 0x62 (fixed, 7-bit)
- **I2C Frequency**: Up to 400 kHz
- **Power Consumption**: Optimized for low power with single-shot mode

### Package
- **Type**: LGA-20 (Land Grid Array)
- **Dimensions**: 10.1 x 10.1 x 6.5 mm
- **Operating Temperature**: -10°C to +60°C
- **Storage Temperature**: -40°C to +70°C

## Pin Configuration

The SCD41 has separate power domains:
- **VDD**: Core power supply (2.4V to 5.5V)
- **VDDH**: Heater power supply (2.4V to 5.5V)
- **GND**: Ground connections
- **SCL/SDA**: I2C communication lines

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("FOR_LOOP")

import ElectricPower
import I2C
import Resistor

from "atopile/sensirion-scd41/sensirion-scd41.ato" import Sensirion_SCD41

module Usage:
    """
    Minimal usage example for `sensirion-scd41`.
    Demonstrates basic CO2, temperature, and humidity sensor setup with I2C interface.
    """

    # --- Main component ---
    co2_sensor = new Sensirion_SCD41

    # --- Power supply ---
    power_3v3 = new ElectricPower
    assert power_3v3.voltage within 3.2V to 3.4V

    # --- I2C bus ---
    i2c_bus = new I2C
    assert i2c_bus.frequency within 100kHz to 400kHz

    # --- Connect interfaces ---
    power_3v3 ~ co2_sensor.power_core
    power_3v3 ~ co2_sensor.power_heater
    i2c_bus ~ co2_sensor.i2c

    # --- Provide I2C bus reference voltage ---
    power_3v3 ~ i2c_bus.scl.reference
    power_3v3 ~ i2c_bus.sda.reference

    # --- I2C address is fixed at 0x62 ---
    assert co2_sensor.i2c.address within 0x62

    # --- I2C pull-up resistors are included in the sensor module ---
    # No external pullup resistors needed

    # --- Usage notes ---
    # The SCD41 measures:
    # - CO2: 400-5000 ppm with ±(40 ppm + 5% of reading) accuracy
    # - Temperature: Built-in SHT4x sensor
    # - Relative Humidity: Built-in SHT4x sensor
    #
    # Features:
    # - Photoacoustic NDIR CO2 sensing
    # - Single-shot measurement mode for low power
    # - Automatic baseline correction
    # - No need for external calibration in most applications

```

## Operation Modes

### Continuous Measurement
- Regular periodic measurements
- Automatic baseline correction active
- Higher power consumption

### Single-Shot Mode
- On-demand measurements
- Ideal for battery-powered applications
- Lower average power consumption

## Important Notes

### Power Supply
- **Clean Power**: Use a quiet power supply with low ripple for best accuracy
- **Decoupling**: 100nF capacitors on both VDD and VDDH are included in the design
- **Dual Rails**: Both core and heater power domains should typically be connected to the same supply

### I2C Communication
- **Fixed Address**: The SCD41 uses a fixed I2C address of 0x62 (no address pins)
- **Pull-ups**: Ensure adequate I2C pull-up resistors (typically 4.7kΩ)
- **Multiple Sensors**: Use I2C multiplexers if multiple SCD41s are needed on the same bus

### Calibration
- **Self-Calibrating**: The sensor includes automatic baseline correction
- **Fresh Air**: Expose to fresh air (≈400 ppm CO2) periodically for best accuracy
- **No Manual Cal**: Manual calibration typically not required for most applications

### Environmental Considerations
- **Airflow**: Ensure adequate airflow around the sensor for accurate readings
- **Avoid Contamination**: Keep away from sources of contamination or strong airflow
- **Warm-up Time**: Allow sensor to stabilize after power-on

## Applications

- **HVAC Systems**: Building ventilation control and monitoring
- **Indoor Air Quality**: Home and office air quality monitoring
- **Industrial Process**: CO2 monitoring in industrial environments
- **Greenhouse Control**: Agricultural CO2 monitoring and control
- **Scientific Instruments**: Laboratory and research applications
- **Smart Buildings**: IoT-enabled environmental monitoring systems

## Advantages over SCD40

- **Extended Range**: 5000 ppm vs 2000 ppm maximum
- **Better Accuracy**: Improved specification for industrial applications
- **Same Interface**: Drop-in replacement with identical I2C interface
- **Single-Shot Mode**: Enhanced low-power operation capability

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
