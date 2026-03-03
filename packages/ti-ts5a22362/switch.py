# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging

import faebryk.library._F as F
import faebryk.core.node as fabll

logger = logging.getLogger(__name__)


class Switch(fabll.Node):
    """
    Switch
    """

    unnamed = [F.Electrical.MakeChild() for _ in range(2)]

    can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )


class PowerSwitch(fabll.Node):
    """
    Power Switch
    """

    unnamed = [F.Electrical.MakeChild() for _ in range(2)]

    can_bridge = fabll.Traits.MakeEdge(
        F.can_bridge.MakeChild(["unnamed[0]"], ["unnamed[1]"])
    )
