# Notes

## Legend

`<manufacturer>`: lower-case, <10 chars

- adi
- ti
- nordic
- bosch
- sensirion
- st
- onsemi
- microchip
- invensense
- nxp
- ublox
- mps

`<part_number>`: non-package related, lower-case

- mcp23017
- bme280
- adxl345
- stm32f767

`<Manufacturer>`: upper-case of `<manufacturer>`

- ADI
- TI
- Nordic
- Bosch

`<Part_Number>`: upper-case of `<part_number>`

- MCP23017
- BME280
- ADXL345
- STM32F767

`<package_name>`: `<manufacturer>`-`<part_number>`

`<module_name>`: `<Manufacturer>`\_`<Part_Number>`

## File Structure

```
/packages/packages/
    <package_name>/
        layouts/
        parts/
        ato.yaml
        <package_name>.ato
        README.md
        usage.ato
```

## <package_name>.ato

```ato
<pragmas>
<stl imports>

<part imports>

module <module_name>:
    """
        <Description of the module>
    """

    # --- External interfaces ---
    example:
    i2c = new I2C
    """
    I²C bus interface (7-bit addr 0x76 / 0x77)
    """
    i2c.required = True

    power = new ElectricPower
    """
    Central power supply for the module feeding the power rails
    """
    power.required = True

    # --- Internal power rails ---
    example:
    power_core = new ElectricPower  # Connects to VDD (sensor core)
    power_core.vcc ~ package.VDD
    power_core.gnd ~ package.GND
    assert power_core.voltage within 1.71V to 3.6V

    # --- Power supply ---

    # --- I²C bus ---
    <addressor>
    <pullups>
    ...

    # --- Decoupling capacitors ---

    # --- I²C pull-ups ---

    # --- <Other configuration> ---

    # --- Package ---
    package = new <package_name>
    <package_connections>
```

Remove empty sections.

## ato.yaml

```yaml
requires-atopile: "^0.10.8"

paths:
  src: ./
  layout: ./layouts

builds:
  default:
    entry: <package_name>.ato:<module_name>
  usage:
    entry: usage.ato:Usage

package:
  identifier: atopile/<package_Name>
  repository: https://github.com/atopile/packages
  homepage: https://github.com/atopile/packages/blob/main/packages/<package_name>/README.md
  version: "0.1.0"
  authors:
    - name: atopile
      email: hi@atopile.io
  summary: `<package_summary>`
  license: MIT
```

`<package_summary>`: Bunch of tags to find the package on the web.
e.g
Tags: Bosch; BME280; Temperature; Humidity; Pressure; Sensor; IC; I2C; Adafruit; <adafruit_product_id>; QWIIC, STEMMA

`<adafruit_product_id>`: Adafruit product ID, e.g `3660` for BME680 (if available)

## usage.ato

```ato
<pragmas>
<stl imports>

<module imports>


module Usage:
    """
    Minimal usage example for `<package_name>`.
    <short description of the example>
    """

    <instance_name> = new <module_name>

    <example usage of module>
    <connect all required interfaces>
    e.g power supply
    e.g i2c bus

    <set required parameters>
    e.g i2c.address = 0x76
```

## README.md

````markdown
# `<verbose_package_name>` e.g Bosch BME280 Temperature, Humidity & Pressure Sensor

`<longer description of the package and main component>`

## Usage

```ato
<copy-paste of usage.ato>
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This package is provided under the [MIT License](https://opensource.org/license/mit/).
````
