# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging

import faebryk.core.node as fabll
import faebryk.library._F as F

logger = logging.getLogger(__name__)


class Switch(fabll.Node):
    """
    Switch with two Electrical terminals that can be bridged.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    unnamed = [F.Electrical.MakeChild() for _ in range(2)]

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )


class PowerSwitch(fabll.Node):
    """
    Power Switch with two ElectricPower terminals that can be bridged.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    unnamed = [F.ElectricPower.MakeChild() for _ in range(2)]

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )
