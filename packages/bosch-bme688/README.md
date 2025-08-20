# Bosch BME688 4-in-1 Environmental Sensor

The Bosch BME688 is a 4-in-1 environmental sensor that measures temperature, humidity, barometric pressure, and volatile organic compounds (VOCs) with AI capabilities. This package provides an atopile driver for the BME688 sensor with both I2C and SPI interface support.

## Features

- **Temperature**: ±1.0°C accuracy (range: -40°C to +85°C)
- **Humidity**: ±3% accuracy (range: 0-100% RH)
- **Pressure**: ±1 hPa absolute accuracy (range: 300-1100 hPa)
- **VOC Gas Sensing**: Detects gases like ethanol, alcohol, carbon monoxide with AI processing
- **Dual Interface**: I2C (default) and SPI communication protocols
- **Operating Voltage**: 1.71V to 3.6V (VDD and VDDIO)
- **Power Consumption**: 2.1μA (sleep) to 12mA (gas measurement)
- **Package**: LGA-8 (3.0mm x 3.0mm)
- **Built-in Features**: I2C pull-ups, comprehensive power filtering, protocol auto-selection

## Usage

```ato
#pragma experiment("TRAITS")
import I2C
import ElectricPower

from "atopile/bosch-bme688/bosch-bme688.ato" import Bosch_BME688

module Usage:
    """
    Usage example for bosch-bme688.
    Shows how to connect the BME688 sensor with I2C interface and power supply.

    The sensor comes with built-in I2C pull-ups and power filtering.
    Just connect power and I2C bus - everything else is handled automatically.
    """

    # Create sensor instance
    sensor = new Bosch_BME688

    # Create I2C bus
    i2c = new I2C
    i2c.frequency = 400kHz  # Fast mode I2C

    # Create power supply
    power = new ElectricPower
    power.voltage = 3.3V  # Recommended voltage

    # Connect interfaces - that's it!
    i2c ~ sensor.i2c
    power ~ sensor.power

    # Address will be 0x77 (SDO floating) or 0x76 (SDO to GND)
    # Built-in features automatically included:
    # - I2C pull-ups (4.7kΩ)
    # - Power filtering (100nF + 10nF caps)
    # - Protocol selection (I2C default)
    assert sensor.i2c.address is 0x77

```

## I2C Address Configuration

The BME688 supports two I2C addresses:
- **0x77**: When SDO pin is floating or connected to VDDIO (default)
- **0x76**: When SDO pin is connected to GND

The address is automatically configured through the built-in addressor interface with proper logic.

## Built-in Features

### Power Supply
- **Dual Rail Design**: Separate VDD (core) and VDDIO (I/O) power supplies
- **Power Filtering**: Each rail has 100nF + 10nF decoupling capacitors
- **Current Specifications**: 2.1μA (sleep) to 12mA (gas measurement)
- **Voltage Range**: 1.71V to 3.6V for both rails

### I2C Interface
- **Built-in Pull-ups**: 4.7kΩ resistors on SCL and SDA lines
- **Frequency Range**: 10kHz to 3.4MHz
- **Automatic Address Selection**: Via SDO pin logic

### SPI Interface
- **Frequency Range**: 1MHz to 10MHz
- **Supported Modes**: Mode 0 (CPOL=0, CPHA=0) and Mode 3 (CPOL=1, CPHA=1)
- **Chip Select**: Integrated with protocol selection logic

## SPI Interface

For SPI communication, use the `spi` interface and `cs` (chip select) pin:

```ato
# Connect SPI interface
spi_bus ~ sensor.spi
cs_pin ~ sensor.cs
```

## Power Supply

The sensor requires dual power supplies:
- **VDD**: Core power supply (1.71V to 3.6V)
- **VDDIO**: I/O power supply (1.71V to 3.6V)

Both rails are internally connected to the main `power` interface and include decoupling capacitors.

## Gas Sensor Notes

- The gas sensor requires a 48-hour initial "burn-in" period for optimal performance
- VOC readings have inherent variability and require calibration for specific applications
- The sensor includes AI capabilities for gas pattern recognition

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit).
