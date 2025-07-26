# Microchip MCP9601 Thermocouple EMF to Temperature Converter

High-precision thermocouple amplifier with integrated cold-junction compensation, open/short-circuit detection, and programmable temperature alerts. The MCP9601 provides ±0.5°C typical accuracy and supports all 8 major thermocouple types for precise temperature monitoring in industrial applications.

## Features

- **High Accuracy**: ±0.5°C (typical), ±1.5°C (maximum) from -40°C to +125°C
- **Universal Thermocouple Support**: Types K, J, T, N, S, E, B, and R with NIST ITS-90 compliance
- **Built-in Safety**: Open-circuit and short-circuit detection with dedicated alert outputs
- **Flexible Alerts**: 4 programmable temperature alert outputs with configurable thresholds
- **Advanced Features**: Digital filtering, burst mode, and selectable ADC resolution (12-18 bit)
- **Low Power**: 300µA typical operation, 2µA shutdown mode
- **Wide Supply Range**: 2.7V to 5.5V operation
- **Robust Communication**: I2C interface with 8 possible addresses (0x60 to 0x67)
- **Default I2C Address**: 0x60 (ADDR pin to GND via 0Ω resistor)
- **Measurement Resolution**: Up to 0.0625°C with 18-bit ADC
- **Fast Conversion**: 5ms to 320ms depending on resolution setting

## Usage

```ato
#pragma experiment("TRAITS")
#pragma experiment("MODULE_TEMPLATING")
#pragma experiment("FOR_LOOP")
#pragma experiment("BRIDGE_CONNECT")
import I2C
import ElectricPower
import Resistor

from "microchip-mcp9601.ato" import Microchip_MCP9601


module Usage:
    """
    Complete usage example for microchip-mcp9601 thermocouple amplifier.
    Demonstrates connecting a K-type thermocouple with I2C and power interfaces,
    plus temperature alert outputs for a complete temperature monitoring system.
    """

    # Main thermocouple amplifier
    sensor = new Microchip_MCP9601

    # External interfaces
    i2c = new I2C
    power = new ElectricPower

    # Thermocouple simulation (in practice, connect actual K-type thermocouple wires here)
    # This resistor represents the thermocouple's differential resistance
    # Replace with actual thermocouple: positive wire (yellow) to thermocouple_positive
    #                                   negative wire (red) to thermocouple_negative
    thermocouple_sim = new Resistor
    thermocouple_sim.resistance = 100ohm +/- 5%  # Typical thermocouple wire resistance
    thermocouple_sim.package = "0603"

    # Connect core interfaces
    i2c ~ sensor.i2c
    power ~ sensor.power

    # Connect thermocouple simulation to sensor inputs
    # In practice: Connect thermocouple wires directly to these inputs
    sensor.thermocouple_positive.line ~> thermocouple_sim ~> sensor.thermocouple_negative.line

    # Set power supply voltage (3.3V typical for thermocouple applications)
    assert power.voltage within 3.0V to 3.6V

    # Optional: Connect alert outputs for temperature monitoring
    # sensor.alert1, sensor.alert2, sensor.alert3, sensor.alert4
    # sensor.oc_alert (open-circuit detection)
    # sensor.sc_alert (short-circuit detection)
```

## Practical Implementation

### Connecting Real Thermocouples

The usage example above shows a resistor for simulation purposes. In practice, connect thermocouple wires directly:

```ato
# Replace the resistor simulation with direct connections:
# thermocouple_positive_wire ~ sensor.thermocouple_positive
# thermocouple_negative_wire ~ sensor.thermocouple_negative
```

### Thermocouple Wire Connections

- **Positive Wire**: Connect to `sensor.thermocouple_positive.line`
- **Negative Wire**: Connect to `sensor.thermocouple_negative.line`
- **Shield/Ground**: Connect to system ground if shielded cables are used

### PCB Layout Considerations

- Keep thermocouple traces short and matched
- Use ground planes for noise reduction
- Place MCP9601 close to thermocouple connector
- Minimize thermal gradients near the IC (cold-junction compensation)

## Thermocouple Types and Applications

The MCP9601 supports all 8 standard thermocouple types defined by NIST ITS-90:

| Type | Materials | Temperature Range | Sensitivity | Common Applications |
|------|-----------|-------------------|-------------|-------------------|
| **K** | Chromel/Alumel | -270°C to +1372°C | ~41µV/°C | General purpose, industrial |
| **J** | Iron/Constantan | -210°C to +1200°C | ~52µV/°C | Older industrial, reducing atmospheres |
| **T** | Copper/Constantan | -270°C to +400°C | ~43µV/°C | Cryogenic, food industry |
| **N** | Nicrosil/Nisil | -270°C to +1300°C | ~39µV/°C | High temperature, oxidizing atmospheres |
| **S** | Platinum/Platinum-Rhodium | -50°C to +1768°C | ~6µV/°C | High temperature, noble metal |
| **E** | Chromel/Constantan | -270°C to +1000°C | ~68µV/°C | Highest sensitivity |
| **B** | Platinum-Rhodium alloys | +250°C to +1820°C | ~0.33µV/°C | Very high temperature |
| **R** | Platinum/Platinum-Rhodium | -50°C to +1768°C | ~6µV/°C | High temperature, laboratory |

### Thermocouple Wiring Colors

**K-Type (most common)**:
- Positive (Chromel): Yellow
- Negative (Alumel): Red

**Standard Color Codes** vary by region. Always verify with thermocouple documentation.

## Applications

- Industrial temperature monitoring
- Petrochemical thermal management
- Hand-held measurement equipment
- Commercial and industrial ovens
- Engine thermal monitoring
- Temperature detection racks
- Process control systems
- HVAC temperature sensing

## Key Differences from MCP9600

- **Enhanced Fault Detection**: Built-in open-circuit and short-circuit detection with dedicated outputs
- **Extended Feature Set**: Additional configuration options and improved diagnostic capabilities
- **Improved Safety**: Better suited for critical industrial applications requiring fault monitoring

## Package Information

- **Footprint**: 20-Lead MQFN (Quad Flat No-Lead)
- **Thermocouple Compatibility**: All NIST ITS-90 standard types
- **Address Configuration**: Single ADDR pin with voltage divider (8 addresses: 0x60-0x67)
- **Temperature Range**: -40°C to +125°C operating, supports thermocouple ranges up to +1800°C

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
