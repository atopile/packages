# AlpsAlpine RS60N11M9A0F Motorized Fader

The AlpsAlpine RS60N11M9A0F is a motorized fader that is used to control the volume of an audio signal.

## Usage

```ato
#pragma experiment("BRIDGE_CONNECT")
#pragma experiment("MODULE_TEMPLATING")

import ElectricPower
import ElectricLogic
import ElectricSignal

from "atopile/alpsalpine-rs60n11m9a0f/alpsalpine-rs60n11m9a0f.ato" import AlpsAlpine_RS60N11M9A0F
from "atopile/ti-drv8210p/ti-drv8210p.ato" import Texas_Instruments_DRV8210PDSGR
from "atopile/st-ldk220/st-ldk220.ato" import LDK220M_R
from "atopile/espressif-esp32-s3/espressif-esp32-s3.ato" import Espressif_ESP32_S3
from "atopile/usb-connectors/usb-connectors.ato" import USB2_0TypeCHorizontalConnector
from "atopile/mounting-holes/MountingHole.py" import MountingHole
from "atopile/logos/logos.ato" import atopile_logo_25x6mm

module Usage:
    """
    Example usage of AlpsAlpine RS60N11M9A0F motor fader with H-bridge driver and resistance sense.
    """
    # this is really important
    logo = new atopile_logo_25x6mm

    # --- External Interfaces ---
    # Instantiate Components
    esp32 = new Espressif_ESP32_S3
    usb_connector = new USB2_0TypeCHorizontalConnector
    motor_driver = new Texas_Instruments_DRV8210PDSGR
    motor_fader = new AlpsAlpine_RS60N11M9A0F
    ldo = new LDK220M_R

    # Power
    power_motor = new ElectricPower
    power_motor.voltage = 5V +/- 5%

    power_logic = new ElectricPower
    power_logic.voltage = 3.3V +/- 5%

    # Logic Input
    in_1 = new ElectricLogic
    in_2 = new ElectricLogic
    sleep = new ElectricLogic

    # Logic Output
    pot_sense = new ElectricSignal
    current_sense = new ElectricSignal
    touch_sense = new ElectricLogic

    # --- Connections ---
    # Power Connections
    usb_connector.usb.usb_if.buspower ~ power_motor

    power_logic ~ esp32.power

    power_motor ~ motor_driver.motor_power
    power_motor ~ motor_fader.motor_power
    power_logic ~ motor_driver.logic_power
    power_logic ~ motor_fader.potentiometer_power

    power_motor ~> ldo ~> power_logic

    esp32.usb ~ usb_connector.usb

    # Motor Connections
    motor_driver.motor_out_2 ~ motor_fader.motor_drive_p
    motor_driver.motor_out_1 ~ motor_fader.motor_drive_n

    # Logic Connections
    in_1 ~ motor_driver.logic_in_1
    in_2 ~ motor_driver.logic_in_2
    sleep ~ motor_driver.n_sleep

    in_1 ~ esp32.io[4]
    in_2 ~ esp32.io[5]
    sleep ~ esp32.io[6]

    pot_sense ~ motor_fader.potentiometer_sense
    current_sense ~ motor_driver.current_sense_voltage

    pot_sense ~ esp32.adc[2]
    current_sense ~ esp32.adc[3]

    touch_sense ~ motor_fader.touch_sense
    touch_sense ~ esp32.touch[1]

    # --- Netnames ---
    power_motor.lv.suggested_net_name = "GND"
    power_motor.hv.suggested_net_name = "VCC_MOTOR"
    power_logic.hv.suggested_net_name = "VCC_LOGIC"
    in_1.line.suggested_net_name = "IN_N"
    in_2.line.suggested_net_name = "IN_P"
    sleep.line.suggested_net_name = "SLEEP"
    pot_sense.line.suggested_net_name = "POT_SENSE"
    current_sense.line.suggested_net_name = "CURRENT_SENSE"
    touch_sense.line.suggested_net_name = "TOUCH_SENSE"

```

## Contributing

Contributions to this package are welcome via pull requests on the GitHub repository.

## License

This atopile package is provided under the [MIT License](https://opensource.org/license/mit/).
