# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.util import once


class can_bridge_symmetric(F.can_bridge.impl()):
    @once
    def _ifs(self):
        ifs = self.get_obj(Module).get_children(direct_only=True, types=ModuleInterface)
        assert len(ifs) == 2
        return ifs

    def get_in(self):
        return self._ifs()[0]

    def get_out(self):
        return self._ifs()[1]
