# Test Points

Various testpoints.

## Usage

```ato
#pragma experiment("MODULE_TEMPLATING")

import ElectricSignal

# Circular and circular SMD testpoints
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D1_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D1_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D2_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D2_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D3_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_D4_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_1_0x1_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_1_5x1_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_2_0x2_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_2_5x2_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_3_0x3_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_SMDPad_4_0x4_0mm

# Rectangular and rectangular THT testpoints
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D1_0mm_Drill_0_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D1_5mm_Drill_0_7mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D2_0mm_Drill_1_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D2_5mm_Drill_1_2mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D3_0mm_Drill_1_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_D4_0mm_Drill_2_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_1_0x1_0mm_Drill_0_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_1_5x1_5mm_Drill_0_7mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_2_0x2_0mm_Drill_1_0mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_2_5x2_5mm_Drill_1_2mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_3_0x3_0mm_Drill_1_5mm
from "atopile/testpoints/testpoints.ato" import TestPoint_THTPad_4_0x4_0mm_Drill_2_0mm

module Usage:
    """
    Example of using testpoints
    """
    test_electrical_signal = new ElectricSignal

    # SMD circular testpoints
    smd_testpointd1_0mm = new TestPoint_SMDPad_D1_0mm
    smd_testpointd1_5mm = new TestPoint_SMDPad_D1_5mm
    smd_testpointd2_0mm = new TestPoint_SMDPad_D2_0mm
    smd_testpointd2_5mm = new TestPoint_SMDPad_D2_5mm
    smd_testpointd3_0mm = new TestPoint_SMDPad_D3_0mm
    smd_testpointd4_0mm = new TestPoint_SMDPad_D4_0mm
    # SMD rectangular testpoints
    smd_testpoint1_0x1_0mm = new TestPoint_SMDPad_1_0x1_0mm
    smd_testpoint1_5x1_5mm = new TestPoint_SMDPad_1_5x1_5mm
    smd_testpoint2_0x2_0mm = new TestPoint_SMDPad_2_0x2_0mm
    smd_testpoint2_5x2_5mm = new TestPoint_SMDPad_2_5x2_5mm
    smd_testpoint3_0x3_0mm = new TestPoint_SMDPad_3_0x3_0mm
    smd_testpoint4_0x4_0mm = new TestPoint_SMDPad_4_0x4_0mm

    # THT circular testpoints
    tht_testpointd1_0mm = new TestPoint_THTPad_D1_0mm_Drill_0_5mm
    tht_testpointd1_5mm = new TestPoint_THTPad_D1_5mm_Drill_0_7mm
    tht_testpointd2_0mm = new TestPoint_THTPad_D2_0mm_Drill_1_0mm
    tht_testpointd2_5mm = new TestPoint_THTPad_D2_5mm_Drill_1_2mm
    tht_testpointd3_0mm = new TestPoint_THTPad_D3_0mm_Drill_1_5mm
    tht_testpointd4_0mm = new TestPoint_THTPad_D4_0mm_Drill_2_0mm
    # THT rectangular testpoints
    tht_testpoint1_0x1_0mm = new TestPoint_THTPad_1_0x1_0mm_Drill_0_5mm
    tht_testpoint1_5x1_5mm = new TestPoint_THTPad_1_5x1_5mm_Drill_0_7mm
    tht_testpoint2_0x2_0mm = new TestPoint_THTPad_2_0x2_0mm_Drill_1_0mm
    tht_testpoint2_5x2_5mm = new TestPoint_THTPad_2_5x2_5mm_Drill_1_2mm
    tht_testpoint3_0x3_0mm = new TestPoint_THTPad_3_0x3_0mm_Drill_1_5mm
    tht_testpoint4_0x4_0mm = new TestPoint_THTPad_4_0x4_0mm_Drill_2_0mm

    # Example connection - connecting all testpoints together
    test_electrical_signal.line ~ smd_testpointd1_0mm.contact
    test_electrical_signal.line ~ smd_testpointd1_5mm.contact
    test_electrical_signal.line ~ smd_testpointd2_0mm.contact
    test_electrical_signal.line ~ smd_testpointd2_5mm.contact
    test_electrical_signal.line ~ smd_testpointd3_0mm.contact
    test_electrical_signal.line ~ smd_testpointd4_0mm.contact

    test_electrical_signal.line ~ smd_testpoint1_0x1_0mm.contact
    test_electrical_signal.line ~ smd_testpoint1_5x1_5mm.contact
    test_electrical_signal.line ~ smd_testpoint2_0x2_0mm.contact
    test_electrical_signal.line ~ smd_testpoint2_5x2_5mm.contact
    test_electrical_signal.line ~ smd_testpoint3_0x3_0mm.contact
    test_electrical_signal.line ~ smd_testpoint4_0x4_0mm.contact

    # Example connection - connecting all THT testpoints together
    test_electrical_signal.line ~ tht_testpointd1_0mm.contact
    test_electrical_signal.line ~ tht_testpointd1_5mm.contact
    test_electrical_signal.line ~ tht_testpointd2_0mm.contact
    test_electrical_signal.line ~ tht_testpointd2_5mm.contact
    test_electrical_signal.line ~ tht_testpointd3_0mm.contact
    test_electrical_signal.line ~ tht_testpointd4_0mm.contact

    test_electrical_signal.line ~ tht_testpoint1_0x1_0mm.contact
    test_electrical_signal.line ~ tht_testpoint1_5x1_5mm.contact
    test_electrical_signal.line ~ tht_testpoint2_0x2_0mm.contact
    test_electrical_signal.line ~ tht_testpoint2_5x2_5mm.contact
    test_electrical_signal.line ~ tht_testpoint3_0x3_0mm.contact
    test_electrical_signal.line ~ tht_testpoint4_0x4_0mm.contact

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
