# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.core.node as fabll
import faebryk.library._F as F


class Switch(fabll.Node):
    """
    Switch
    """

    unnamed = [F.Electrical.MakeChild() for _ in range(2)]

    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )


class PowerSwitch(fabll.Node):
    """
    Power Switch
    """

    unnamed = [F.ElectricPower.MakeChild() for _ in range(2)]

    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )
