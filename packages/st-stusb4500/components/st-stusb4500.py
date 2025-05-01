# SPDX-License-Identifier: MIT

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.units import P  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.picker.picker import DescriptiveProperties

# Components
from .ESDA25W import ESDA25W
from .ESDA25P35_1U1M import ESDA25P35_1U1M


class _STUSB4500QTR(Module):
    """
    Controller I2C QFN-24-EP(4x4) USB Converters ROHS
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    # TODO: Change auto-generated interface types to actual high level types
    VREG_2V7: F.ElectricPower
    VREG_1V2: F.ElectricPower
    VDD: F.ElectricPower

    CC1: F.ElectricLogic
    CC2: F.ElectricLogic
    CC1DB: F.ElectricLogic
    CC2DB: F.ElectricLogic

    I2C: F.I2C

    ATTACH: F.Electrical
    GPIO: F.Electrical
    ADDR1: F.Electrical
    POWER_OK3: F.Electrical
    NC: F.Electrical
    POWER_OK2: F.Electrical
    ALERT: F.Electrical
    VBUS_EN_SNK: F.Electrical
    EP: F.Electrical
    A_B_SIDE: F.Electrical
    VSYS: F.Electrical
    DISCH: F.Electrical
    VBUS_VS_DISCH: F.Electrical
    RESET: F.Electrical
    ADDR0: F.Electrical

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    lcsc_id = L.f_field(F.has_descriptive_properties_defined)({"LCSC": "C2678061"})
    designator_prefix = L.f_field(F.has_designator_prefix)("U")
    descriptive_properties = L.f_field(F.has_descriptive_properties_defined)(
        {
            DescriptiveProperties.manufacturer: "STMicroelectronics",
            DescriptiveProperties.partno: "STUSB4500QTR",
        }
    )
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://www.lcsc.com/datasheet/lcsc_datasheet_2106070703_STMicroelectronics-STUSB4500QTR_C2678061.pdf"
    )

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={
                self.ADDR0: ["ADDR0"],
                self.ADDR1: ["ADDR1"],
                self.ALERT: ["ALERT"],
                self.ATTACH: ["ATTACH"],
                self.A_B_SIDE: ["A_B_SIDE"],
                self.CC1.line: ["CC1"],
                self.CC1DB.line: ["CC1DB"],
                self.CC2.line: ["CC2"],
                self.CC2DB.line: ["CC2DB"],
                self.DISCH: ["DISCH"],
                self.EP: ["EP"],
                self.VDD.lv: ["GND"],
                self.GPIO: ["GPIO"],
                self.POWER_OK2: ["POWER_OK2"],
                self.POWER_OK3: ["POWER_OK3"],
                self.RESET: ["RESET"],
                self.I2C.scl.line: ["SCL"],
                self.I2C.sda.line: ["SDA"],
                self.VBUS_EN_SNK: ["VBUS_EN_SNK"],
                self.VBUS_VS_DISCH: ["VBUS_VS_DISCH"],
                self.VDD.hv: ["VDD"],
                self.VREG_1V2.hv: ["VREG_1V2"],
                self.VREG_2V7.hv: ["VREG_2V7"],
                self.VSYS: ["VSYS"],
            },
            accept_prefix=False,
            case_sensitive=False,
            nc=["NC"],
        )

    def __preinit__(self):
        self.VREG_1V2.voltage.constrain_subset(L.Range(1.1 * P.V, 1.3 * P.V))
        self.VREG_2V7.voltage.constrain_subset(L.Range(2.6 * P.V, 2.8 * P.V))

        self.VDD.lv.connect(
            self.VREG_2V7.lv, self.VREG_1V2.lv, self.EP, self.RESET, self.VSYS, self.NC
        )

        # Set address
        self.ADDR0.connect(self.VDD.lv)
        self.ADDR1.connect(self.VDD.lv)


class STUSB4500QTR(Module):
    pd_controller: _STUSB4500QTR
    # USB_CONNECTOR: HCTL_HC_TYPE_C_24P_VS9_3_5A_F1_1_04
    esd_cc: ESDA25W
    vsink_mosfet: F.MOSFET

    power_vbus: F.ElectricPower  # input from USB connector
    power_mcu: F.ElectricPower  # input from processor
    i2c: F.I2C
    # cc = L.list_field(2, F.ElectricLogic)
    cc1: F.ElectricLogic
    cc2: F.ElectricLogic  # hack to make it work with ato
    power_vsink: F.ElectricPower  # output to power supply
    i2c: F.I2C

    # Passive components
    vbus_vs_disch_r: F.Resistor
    vreg_2v7_cap: F.Capacitor
    vreg_1v2_cap: F.Capacitor
    vbus_cap: F.Capacitor
    vbus_esd_diode: ESDA25P35_1U1M
    vsink_esd_diode: ESDA25P35_1U1M
    vsink_gate_r: F.Resistor
    vsink_gate_pullup: F.Resistor
    vsink_gate_snub_r: F.Resistor
    vsink_gate_snub_c: F.Capacitor
    disch_r: F.Resistor

    def __preinit__(self):
        # Tie gnd together
        self.power_vsink.lv.connect(
            self.power_vbus.lv,
            self.power_mcu.lv,
            self.pd_controller.VDD.lv,
            self.pd_controller.VREG_1V2.lv,
            self.pd_controller.VREG_2V7.lv,
        )

        F.ElectricLogic.connect_all_module_references(self, gnd_only=True)

        # USB connector
        self.cc1.connect(self.pd_controller.CC1, self.pd_controller.CC1DB)
        self.cc2.connect(self.pd_controller.CC2, self.pd_controller.CC2DB)

        self.vbus_vs_disch_r.resistance.constrain_subset(
            L.Range.from_center_rel(1 * P.kohm, 0.01)
        )
        self.vbus_vs_disch_r.add(F.has_package("R0402"))
        self.power_vbus.hv.connect_via(
            self.vbus_vs_disch_r, self.pd_controller.VBUS_VS_DISCH
        )

        # I2C
        self.i2c.connect(self.pd_controller.I2C)

        # Internal rail decoupling
        self.vreg_2v7_cap.unnamed[0].connect(self.pd_controller.VREG_2V7.lv)
        self.vreg_2v7_cap.unnamed[1].connect(self.pd_controller.VREG_2V7.hv)
        self.vreg_2v7_cap.capacitance.constrain_subset(
            L.Range.from_center_rel(1 * P.uF, 0.2)
        )
        self.vreg_2v7_cap.add(F.has_package("C0402"))

        self.vreg_1v2_cap.unnamed[0].connect(self.pd_controller.VREG_1V2.lv)
        self.vreg_1v2_cap.unnamed[1].connect(self.pd_controller.VREG_1V2.hv)
        self.vreg_1v2_cap.capacitance.constrain_subset(
            L.Range.from_center_rel(1 * P.uF, 0.2)
        )
        self.vreg_1v2_cap.add(F.has_package("C0402"))

        # Regulator rail net naming
        # vreg_2v7 = F.Net.with_name("VREG_2V7")
        # vreg_1v2 = F.Net.with_name("VREG_1V2")
        # vreg_2v7.part_of.connect(self.pd_controller.VREG_2V7.hv)
        # vreg_1v2.part_of.connect(self.pd_controller.VREG_1V2.hv)

        self.vbus_cap.unnamed[0].connect(self.power_vbus.lv)
        self.vbus_cap.unnamed[1].connect(self.power_vbus.hv)
        self.vbus_cap.capacitance.constrain_subset(
            L.Range.from_center_rel(4.7 * P.uF, 0.3)
        )
        self.vbus_cap.add(F.has_package("C0603"))
        self.vbus_cap.max_voltage.constrain_subset(
            L.Range(30 * P.V, float("inf") * P.V)
        )

        self.power_vbus.connect(self.pd_controller.VDD)

        # VBUS net naming
        # vbus = F.Net.with_name("VBUS")
        # vbus.part_of.connect(self.power_vbus.hv)

        # ESD protection
        self.power_vbus.hv.connect_via(self.vbus_esd_diode, self.power_vbus.lv)
        self.power_vsink.hv.connect_via(self.vsink_esd_diode, self.power_vsink.lv)
        self.pd_controller.CC1.line.connect(self.esd_cc.K1)
        self.pd_controller.CC2.line.connect(self.esd_cc.K2)
        self.power_vbus.lv.connect(self.esd_cc.A)

        # CC line net naming
        # cc1 = F.Net.with_name("CC1")
        # cc2 = F.Net.with_name("CC2")
        # cc1.part_of.connect(self.pd_controller.CC1.line)
        # cc2.part_of.connect(self.pd_controller.CC2.line)

        # VSINK SWITCH
        # self.VSINK_MOSFET.channel_type.alias_is(F.MOSFET.ChannelType.P_CHANNEL)
        self.vsink_mosfet.add(F.has_descriptive_properties_defined({"LCSC": "C471913"}))
        # VBUS to VSINK switching
        self.power_vbus.hv.connect_via(self.vsink_mosfet, self.power_vsink.hv)

        # VSINK voltage divider for VCC
        # self.VSINK_VCC = F.Net.with_name("VSINK_VCC")
        # self.VSINK_VCC.part_of.connect(self.power_vsink.hv)

        # Gate pullup resistor divider
        self.vsink_gate_r.resistance.constrain_subset(
            L.Range.from_center_rel(22 * P.kohm, 0.03)
        )
        self.vsink_gate_r.add(F.has_package("R0402"))
        self.vsink_mosfet.gate.connect_via(
            self.vsink_gate_r, self.pd_controller.VBUS_EN_SNK
        )

        # Gate to drain pullup resistor
        self.vsink_gate_pullup.resistance.constrain_subset(
            L.Range.from_center_rel(100 * P.kohm, 0.02)
        )
        self.vsink_gate_pullup.add(F.has_package("R0402"))
        self.vsink_mosfet.gate.connect_via(
            self.vsink_gate_pullup, self.vsink_mosfet.drain
        )

        # Gate to source RC snubber
        self.vsink_gate_snub_r.resistance.constrain_subset(
            L.Range.from_center_rel(100 * P.ohm, 0.01)
        )
        self.vsink_gate_snub_r.add(F.has_package("R0402"))

        self.vsink_gate_snub_c.capacitance.constrain_subset(
            L.Range.from_center_rel(100 * P.nF, 0.2)
        )
        self.vsink_gate_snub_c.add(F.has_package("C0402"))

        # Connect RC snubber between gate and source
        self.vsink_mosfet.gate.connect_via(
            [self.vsink_gate_snub_r, self.vsink_gate_snub_c], self.vsink_mosfet.source
        )

        # DISCH resistor
        self.disch_r.resistance.constrain_subset(
            L.Range.from_center_rel(1 * P.kohm, 0.01)
        )
        self.disch_r.add(F.has_package("R0402"))
        self.power_vbus.hv.connect_via(self.disch_r, self.pd_controller.DISCH)

        # I2C nets
        # self.i2c_scl = F.Net.with_name("I2C_SCL")
        # self.i2c_sda = F.Net.with_name("I2C_SDA")
        # self.i2c.scl.line.connect(self.i2c_scl.part_of)
        # self.i2c.sda.line.connect(self.i2c_sda.part_of)

        self.i2c.connect(self.pd_controller.I2C)

        self.i2c.terminate(owner=self)
        for line in [self.i2c.sda, self.i2c.scl]:
            for r in line.get_trait(F.ElectricLogic.has_pulls).get_pulls():
                if r is None:
                    continue
                r.resistance.constrain_subset(
                    L.Range.from_center_rel(4.7 * P.kohm, 0.03)
                )
                r.add(F.has_package("R0402"))

        F.ElectricLogic.connect_all_node_references([self.power_mcu] + [self.i2c])
        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.power_vsink.voltage.constrain_superset(L.Range(5 * P.V, 20 * P.V))
        self.power_vbus.voltage.constrain_superset(L.Range(5 * P.V, 20 * P.V))
        self.power_mcu.voltage.constrain_subset(L.Range(0 * P.V, 3.6 * P.V))
