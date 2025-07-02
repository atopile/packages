# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P


class ResistorWithMapping(Module):
    resistor: F.Resistor
    input_current_limit = L.p_field(units=P.A)
    battery_voltage_limit = L.p_field(units=P.V)

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(*self.resistor.unnamed)

    def __preinit__(self):
        self.input_current_limit.constrain_mapping(
            self.battery_voltage_limit,
            {
                500 * P.mA: L.Range(3.0 * P.V, 4.1 * P.V),
                1100 * P.mA: L.Range(3.0 * P.V, 4.1 * P.V),
                500 * P.mA: L.Range(3.0 * P.V, 4.4 * P.V),
                1100 * P.mA: L.Range(3.0 * P.V, 4.4 * P.V),
                500 * P.mA: L.Range(3.0 * P.V, 4.35 * P.V),
                1100 * P.mA: L.Range(3.0 * P.V, 4.35 * P.V),
                100 * P.mA: L.Range(3.0 * P.V, 4.2 * P.V),
                500 * P.mA: L.Range(3.0 * P.V, 4.2 * P.V),
                1100 * P.mA: L.Range(3.0 * P.V, 4.2 * P.V),
                500 * P.mA: L.Range(3.0 * P.V, 4.05 * P.V),
                1100 * P.mA: L.Range(3.0 * P.V, 4.05 * P.V),
                1100 * P.mA: L.Range(2.0 * P.V, 3.65 * P.V),
                500 * P.mA: L.Range(2.0 * P.V, 3.6 * P.V),
                1100 * P.mA: L.Range(2.0 * P.V, 3.6 * P.V),
            },
        )

        self.input_current_limit.constrain_mapping(
            self.resistor.resistance,
            {
                500 * P.mA: L.Range.from_center_rel(130 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(100 * P.kohm, 0.01),
                500 * P.mA: L.Range.from_center_rel(75 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(56 * P.kohm, 0.01),
                500 * P.mA: L.Range.from_center_rel(43 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(33 * P.kohm, 0.01),
                100 * P.mA: L.Range.from_center_rel(24 * P.kohm, 0.01),
                500 * P.mA: L.Range.from_center_rel(18 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(13 * P.kohm, 0.01),
                500 * P.mA: L.Range.from_center_rel(9.1 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(6.8 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(5.1 * P.kohm, 0.01),
                500 * P.mA: L.Range.from_center_rel(3.6 * P.kohm, 0.01),
                1100 * P.mA: L.Range.from_center_rel(2.4 * P.kohm, 0.01),
            },
        )
