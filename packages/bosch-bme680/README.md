# Bosch BME680 4-in-1 Environmental Sensor

The BME680 is a digital 4-in-1 sensor with gas, humidity, pressure and temperature measurement from Bosch Sensortec. It features gas sensing capability for indoor air quality monitoring, with temperature accuracy of ±1.0°C, humidity accuracy of ±3%, and pressure accuracy of ±1 hPa.

## Usage

```ato
#pragma experiment("TRAITS")
import I2C
import ElectricPower

from "atopile/bosch-bme680/bosch-bme680.ato" import Bosch_BME680

module Usage:
    """
    Usage example for bosch-bme680.
    Shows how to connect the BME680 sensor with I2C interface and power supply.

    The sensor comes with built-in I2C pull-ups and power filtering.
    Just connect power and I2C bus - everything else is handled automatically.
    """

    # Create sensor instance
    sensor = new Bosch_BME680

    # Create I2C bus
    i2c = new I2C
    i2c.frequency = 400kHz  # Fast mode I2C

    # Create power supply
    power = new ElectricPower
    power.voltage = 3.3V  # Recommended voltage

    # Connect interfaces - that's it!
    i2c ~ sensor.i2c
    power ~ sensor.power

    # Address will be 0x76 (SDO to GND) or 0x77 (SDO floating)
    # Built-in features automatically included:
    # - I2C pull-ups (10kΩ)
    # - Power filtering (100nF caps)
    # - Protocol selection (I2C default)
    # - Dual rail support (VDD/VDDIO internally connected)
    assert sensor.i2c.address is 0x76

```

## Features

- **Temperature**: ±1.0°C accuracy, -40°C to +85°C range
- **Humidity**: ±3% accuracy, 0-100% RH range
- **Pressure**: ±1 hPa accuracy, 300-1100 hPa range
- **Gas**: VOC sensing with programmable heater for air quality monitoring
- **Interfaces**: I2C (default) and SPI with automatic protocol selection
- **Power**: 1.71V to 3.6V operation, ultra-low power consumption
- **Built-in**: I2C pull-ups, power filtering, protocol selection, dual rail support

## Configuration

- **I2C Address**: 0x76 (SDO to GND) or 0x77 (SDO floating/high)
- **I2C Speed**: Up to 3.4MHz supported
- **SPI Speed**: Up to 10MHz supported
- **Power Consumption**: 2.1μA (sleep) to 12mA (gas measurement)
- **Package**: LGA-8 (3.0 × 3.0 × 0.93 mm)

## Built-in Components

This driver automatically includes:
- I2C pull-up resistors (10kΩ on SCL/SDA)
- Power decoupling capacitors (100nF on VDD and VDDIO)
- CS pull-up for I2C mode selection
- Dual power rail support (VDD/VDDIO automatically connected to main power)

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
