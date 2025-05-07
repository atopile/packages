# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.library import L
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class TI_I2C_Addressor(ModuleInterface):
    address = L.p_field(domain=L.Domains.Numbers.NATURAL())
    offset = L.p_field(domain=L.Domains.Numbers.NATURAL())
    base = L.p_field(domain=L.Domains.Numbers.NATURAL())

    # Interfaces
    address_line: F.ElectricLogic
    i2c: F.I2C
    power: F.ElectricPower

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self) -> None:
        for x in (self.address, self.offset, self.base):
            x.constrain_ge(0)

        self.address.alias_is(self.base + self.offset)

        if self.offset == 0:
            self.address_line.line.connect(self.power.gnd)
        elif self.offset == 1:
            self.address_line.line.connect(self.power.vcc)
        elif self.offset == 2:
            self.address_line.line.connect(self.i2c.sda)
        elif self.offset == 3:
            self.address_line.line.connect(self.i2c.scl)
        else:
            raise ValueError("Offset must be 0, 1, 2 or 3")
