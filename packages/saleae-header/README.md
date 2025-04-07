## Overview

Header configured for use with Saleae debug probes, includes interfaces for signals (io + gnd) as well as a few generic interfaces like I2C and spi. So you can monitor your spi bus as easily as saleae.spi ~ micro.spi !

![Saleae Debug Header](https://firebasestorage.googleapis.com/v0/b/atopile.appspot.com/o/saleae-debug-header.png?alt=media&token=84e11ffe-b67d-438b-ae7e-e35b59780a78 "Saleae Debug Header")

## Usage Example

```
import saleae-header from "saleae-header/saleae-header.ato"
import Power from "generics/interfaces.ato"

module SaleaeDebugHeader:
    # Power interface
    power = new Power
    
    # Header for debugging
    debug_header = new saleae-header
    debug_header.pins = 8  # Assuming an 8-pin header for simplicity

    # Manual Signal Definitions
    signal sclk
    signal miso
    signal mosi
    signal cs
    signal scl
    signal sda
    signal vcc
    signal gnd

    # Connections for SPI-like signals
    sclk ~ debug_header.pin1
    miso ~ debug_header.pin2
    mosi ~ debug_header.pin3
    cs ~ debug_header.pin4

    # Connections for I2C-like signals
    scl ~ debug_header.pin5
    sda ~ debug_header.pin6

    # Connections for Power and Ground
    vcc ~ debug_header.pin7
    gnd ~ debug_header.pin8


```

## Features

### Debug Interface: 
Configured for direct connection with Saleae logic analyzers.

### Signal Access: 

Provides easy access to signals for monitoring and debugging.

### SPI Interface: 

Includes connections for SPI bus monitoring.

### I2C Interface: 
Includes connections for I2C bus monitoring.

### Power Connections: 
Accommodates power (VCC) and ground (GND) for the probe.


## Contributing
Contribute to this package using pull requests.

## License
This battery connector module is provided under the MIT License.

## Contact
For further inquiries or support, please contact me at narayan@atopile.io.

