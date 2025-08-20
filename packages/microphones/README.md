# Microphones

A collection of microphones with digital (PMD, I2S) and analog interfaces.

## Usage

```ato
import ElectricPower
import I2S
import ElectricSignal
import PDM

from "atopile/microphones/knowles_sph0641lu4h_1.ato" import Knowles_SPH0641LU4H_1
from "atopile/microphones/linkmems_lma3722t421_oa5.ato" import LinkMems_LMA3722T421_OA5
from "atopile/microphones/linkmems_lmd2718t261_oa1.ato" import LinkMems_LMD2718T261_OA1
from "atopile/microphones/tdk_invensense_ics_43434.ato" import TDK_InvenSense_ICS_43434
from "atopile/microphones/tdk_mmict390200012.ato" import TDK_InvenSense_MMICT390200012

module Usage:
    """
    Minimal example of how to use the Knowles SPH0641LU4H I2S microphone.
    """

    microphone_i2s_1 = new Knowles_SPH0641LU4H_1
    microphone_i2s_2 = new TDK_InvenSense_ICS_43434
    microphone_analog_with_preamp = new LinkMems_LMA3722T421_OA5
    microphone_pdm_1_8v = new LinkMems_LMD2718T261_OA1
    microphone_pdm_3v3 = new TDK_InvenSense_MMICT390200012

    power_3v3 = new ElectricPower
    power_1v8 = new ElectricPower
    power_3v3 ~ microphone_pdm_3v3.power
    power_3v3 ~ microphone_i2s_2.power
    power_3v3 ~ microphone_i2s_1.power
    power_3v3 ~ microphone_analog_with_preamp.power
    power_1v8 ~ microphone_pdm_1_8v.power

    i2s = new I2S
    i2s ~ microphone_i2s_1.i2s
    i2s ~ microphone_i2s_2.i2s

    analog = new ElectricSignal
    analog ~ microphone_analog_with_preamp.analog

    pdm = new PDM
    pdm ~ microphone_pdm_3v3.pdm
    microphone_pdm_3v3.pdm.select.line ~ microphone_pdm_3v3.pdm.select.reference.hv # select L/R channel

    pdm_1_8v = new PDM
    pdm_1_8v ~ microphone_pdm_1_8v.pdm
    microphone_pdm_1_8v.pdm.select.line ~ microphone_pdm_1_8v.pdm.select.reference.hv # select L/R channel

```

```ato
from "atopile/microphones/linkmems_ldm2718t261_oa1.ato" import LinkMems_LMD2718T261_OA1


module LinkMems_LMD2718T261_OA1_example:
    """
    Minimal example of how to use the LinkMems LMD2718T261-OA1 PDM microphone.
    """
    microphone = new LinkMems_LMD2718T261_OA1

    power_3v3 = new ElectricPower
    power_3v3 ~ microphone.power

    pdm = new PDM
    pdm ~ microphone.pdm
    microphone.pdm.select.line ~ power_3v3.lv
```

```ato
from "atopile/microphones/tdk_invensense_mmict390200012.ato" import TDK_InvenSense_MMICT390200012


module TDK_InvenSense_MMICT390200012_example:
    """
    Minimal example of how to use the TDK InvenSense MMICT390200012 PDM microphone.
    """
    microphone = new TDK_InvenSense_MMICT390200012

    power_3v3 = new ElectricPower
    power_3v3 ~ microphone.power

    pdm = new PDM
    pdm ~ microphone.pdm
    microphone.pdm.select.line ~ power_3v3.lv
```

```ato
from "atopile/microphones/tdk_invensense_ics_43434.ato" import TDK_InvenSense_ICS_43434

module TDK_InvenSense_ICS_43434_example:
    """
    Minimal example of how to use the TDK InvenSense ICS-43434 I2S microphone.
    """
    microphone = new TDK_InvenSense_ICS_43434

    power_3v3 = new ElectricPower
    power_3v3 ~ microphone.power

    i2s = new I2S
    i2s ~ microphone.i2s
```

```ato
from "atopile/microphones/knowles_sph0641lu4h_1.ato" import Knowles_SPH0641LU4H_1

module Knowles_SPH0641LU4H_1_example:
    """
    Minimal example of how to use the Knowles SPH0641LU4H I2S microphone.
    """
    microphone = new Knowles_SPH0641LU4H_1

    power_3v3 = new ElectricPower
    power_3v3 ~ microphone.power

    i2s = new I2S
    i2s ~ microphone.i2s
```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
