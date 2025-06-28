# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.library import L
from faebryk.libs.units import P


logger = logging.getLogger(__name__)


class TAS_addressor(ModuleInterface):
    address = L.p_field(domain=L.Domains.Numbers.NATURAL())
    offset = L.p_field(domain=L.Domains.Numbers.NATURAL())
    base = L.p_field(domain=L.Domains.Numbers.NATURAL())
    num_addresses = L.p_field(domain=L.Domains.Numbers.NATURAL())
    address_line: F.ElectricLogic
    addr_resistor: F.Resistor
    i2c: F.I2C

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self) -> None:
        for x in (self.address, self.offset, self.base):
            x.constrain_ge(0)

        self.address.alias_is(self.base + self.offset)

        resistance_values = [
            L.Range.from_center_rel(0 * P.ohm, 0),
            L.Range.from_center_rel(1 * P.kohm, 0.1),
            L.Range.from_center_rel(4.7 * P.kohm, 0.1),
            L.Range.from_center_rel(15 * P.kohm, 0.1),
        ]

        for i, r_val in enumerate(resistance_values):
            (self.offset.operation_is_subset(i)).if_then_else(
                lambda r_val=r_val: self.addr_resistor.resistance.constrain_subset(r_val)
            )
