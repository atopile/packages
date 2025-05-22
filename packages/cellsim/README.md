# TCA9548APWR I2C Multiplexer

## Usage

```
component Connector:
    pins = new Electrical[20]

module Test:
    # Create components
    cellsims = new CellSim8Ch[2]
    connector = new Connector

    # Create power rails
    power_24v = new ElectricPower
    power_3v3 = new ElectricPower

    # Coms
    i2c = new I2C

    # Connect cellsims to power and i2c
    for cellsim in cellsims:
        cellsim.i2c ~ i2c
        cellsim.power_24v ~ power_24v
        cellsim.power_3v3 ~ power_3v3

    # Connect cellsim blocks in series
    cellsims[0].block_up ~ cellsims[1].block_down

    # Cells to conector
    cellsims[0].cell_outputs[0] ~ connector.pins[0]
    cellsims[0].cell_outputs[1] ~ connector.pins[1]
    cellsims[0].cell_outputs[2] ~ connector.pins[2]
    cellsims[0].cell_outputs[3] ~ connector.pins[3]
    cellsims[0].cell_outputs[4] ~ connector.pins[4]
    cellsims[0].cell_outputs[5] ~ connector.pins[5]
    cellsims[0].cell_outputs[6] ~ connector.pins[6]
    cellsims[0].cell_outputs[7] ~ connector.pins[7]
    cellsims[0].cell_outputs[8] ~ connector.pins[8]
    # This is already connected with the block_up/block_down
    # cellsims[1].cell_outputs[0] ~ connector.pins[8]
    cellsims[1].cell_outputs[1] ~ connector.pins[9]
    cellsims[1].cell_outputs[2] ~ connector.pins[10]
    cellsims[1].cell_outputs[3] ~ connector.pins[11]
    cellsims[1].cell_outputs[4] ~ connector.pins[12]
    cellsims[1].cell_outputs[5] ~ connector.pins[13]
    cellsims[1].cell_outputs[6] ~ connector.pins[14]
    cellsims[1].cell_outputs[7] ~ connector.pins[15]
    cellsims[1].cell_outputs[8] ~ connector.pins[16]

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
