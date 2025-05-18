# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class BridgableLogic(Module):
    data_in: F.ElectricLogic
    data_out: F.ElectricLogic

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.data_in, self.data_out)
