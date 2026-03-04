# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import math

import faebryk.core.node as fabll
import faebryk.library._F as F


# Constants for filter calculations
# max_balance_current = 100mA
_BLEED_R = (4.25 / 0.1) / 2  # 21.25 ohm
_BLEED_C = 1 / (_BLEED_R * 2 * math.pi * 80000)  # ~93.6nF
_BLEED_POWER_MIN = (4.25 / 2) ** 2 / _BLEED_R  # ~0.2124W

NUM_CELLS = 16


class SenseFilter(fabll.Node):
    """
    RC low-pass filter between cell power and sense inputs.
    Resistance: 200 ohm +/- 1%, Capacitance: 10nF +/- 20%
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    cell_power = F.ElectricPower.MakeChild()
    sense_input = F.DifferentialPair.MakeChild()

    sense_resistor = F.Resistor.MakeChild()
    sense_capacitor = F.Capacitor.MakeChild()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # ----------------------------------------
    #            Connections
    # ----------------------------------------
    # Topology: cell_power.hv ~> resistor ~> sense_input.p.line
    #           sense_input.p.line ~> capacitor ~> sense_input.n.line
    _connections = [
        # cell_power.hv ~ sense_resistor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [cell_power, F.ElectricPower.hv],
            [sense_resistor, F.Resistor.unnamed[0]],
        ),
        # sense_resistor.unnamed[1] ~ sense_input.p.line
        fabll.is_interface.MakeConnectionEdge(
            [sense_resistor, F.Resistor.unnamed[1]],
            [sense_input, F.DifferentialPair.p, F.ElectricSignal.line],
        ),
        # sense_input.p.line ~ sense_capacitor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [sense_input, F.DifferentialPair.p, F.ElectricSignal.line],
            [sense_capacitor, F.Capacitor.unnamed[0]],
        ),
        # sense_capacitor.unnamed[1] ~ sense_input.n.line
        fabll.is_interface.MakeConnectionEdge(
            [sense_capacitor, F.Capacitor.unnamed[1]],
            [sense_input, F.DifferentialPair.n, F.ElectricSignal.line],
        ),
    ]

    # ----------------------------------------
    #            Constraints
    # ----------------------------------------
    # Sense filter: 200 ohm +/- 1%, 10nF +/- 20%
    _constraints = [
        F.Literals.Numbers.MakeChild_SetSuperset(
            [sense_resistor, F.Resistor.resistance],
            198.0, 202.0, unit=F.Units.Ohm,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [sense_capacitor, F.Capacitor.capacitance],
            8e-9, 12e-9, unit=F.Units.Farad,
        ),
    ]


class BalanceFilter(fabll.Node):
    """
    Dual RC filter for cell balancing.
    Top filter: cell_power.hv -> resistor -> balance_input.p.line
    Bottom filter: cell_power.lv -> resistor -> balance_input.n.line
    Bridge capacitor connects balance_input.n to lower cell for transient filtering.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    cell_power = F.ElectricPower.MakeChild()
    balance_input = F.DifferentialPair.MakeChild()
    cap_bridge_connect = F.ElectricSignal.MakeChild()

    top_resistor = F.Resistor.MakeChild()
    bot_resistor = F.Resistor.MakeChild()
    top_capacitor = F.Capacitor.MakeChild()
    bot_capacitor = F.Capacitor.MakeChild()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # ----------------------------------------
    #            Connections
    # ----------------------------------------
    _connections = [
        # cell_power.hv ~ top_resistor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [cell_power, F.ElectricPower.hv],
            [top_resistor, F.Resistor.unnamed[0]],
        ),
        # top_resistor.unnamed[1] ~ balance_input.p.line
        fabll.is_interface.MakeConnectionEdge(
            [top_resistor, F.Resistor.unnamed[1]],
            [balance_input, F.DifferentialPair.p, F.ElectricSignal.line],
        ),
        # cell_power.lv ~ bot_resistor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [cell_power, F.ElectricPower.lv],
            [bot_resistor, F.Resistor.unnamed[0]],
        ),
        # bot_resistor.unnamed[1] ~ balance_input.n.line
        fabll.is_interface.MakeConnectionEdge(
            [bot_resistor, F.Resistor.unnamed[1]],
            [balance_input, F.DifferentialPair.n, F.ElectricSignal.line],
        ),
        # balance_input.p.line ~ top_capacitor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [balance_input, F.DifferentialPair.p, F.ElectricSignal.line],
            [top_capacitor, F.Capacitor.unnamed[0]],
        ),
        # top_capacitor.unnamed[1] ~ balance_input.n.line
        fabll.is_interface.MakeConnectionEdge(
            [top_capacitor, F.Capacitor.unnamed[1]],
            [balance_input, F.DifferentialPair.n, F.ElectricSignal.line],
        ),
        # balance_input.n.line ~ bot_capacitor.unnamed[0]
        fabll.is_interface.MakeConnectionEdge(
            [balance_input, F.DifferentialPair.n, F.ElectricSignal.line],
            [bot_capacitor, F.Capacitor.unnamed[0]],
        ),
        # bot_capacitor.unnamed[1] ~ cap_bridge_connect.line
        fabll.is_interface.MakeConnectionEdge(
            [bot_capacitor, F.Capacitor.unnamed[1]],
            [cap_bridge_connect, F.ElectricSignal.line],
        ),
    ]

    # ----------------------------------------
    #            Constraints
    # ----------------------------------------
    # Balance filter: bleed resistance ~21.25 ohm +/- 5%
    _constraints = [
        F.Literals.Numbers.MakeChild_SetSuperset(
            [top_resistor, F.Resistor.resistance],
            _BLEED_R * 0.95, _BLEED_R * 1.05, unit=F.Units.Ohm,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [bot_resistor, F.Resistor.resistance],
            _BLEED_R * 0.95, _BLEED_R * 1.05, unit=F.Units.Ohm,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [top_capacitor, F.Capacitor.capacitance],
            _BLEED_C * 0.80, _BLEED_C * 1.20, unit=F.Units.Farad,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [bot_capacitor, F.Capacitor.capacitance],
            _BLEED_C * 0.80, _BLEED_C * 1.20, unit=F.Units.Farad,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [top_resistor, F.Resistor.max_power],
            _BLEED_POWER_MIN, 10.0, unit=F.Units.Watt,
        ),
        F.Literals.Numbers.MakeChild_SetSuperset(
            [bot_resistor, F.Resistor.max_power],
            _BLEED_POWER_MIN, 10.0, unit=F.Units.Watt,
        ),
    ]


def _build_input_filter_connections(
    cell_inputs, sense_inputs, balance_inputs,
    sense_filters, balance_filters, bottom_sense_filter,
):
    """Build connections for ADBMS6830InputFilters.

    Extracted to module-level function to avoid Python 3 class-scope
    list comprehension visibility issue.
    """
    return (
        # Connect cell inputs to sense filters
        [
            fabll.is_interface.MakeConnectionEdge(
                [cell_inputs[i]],
                [sense_filters[i], SenseFilter.cell_power],
            )
            for i in range(NUM_CELLS)
        ]
        # Connect sense filter outputs to sense inputs
        + [
            fabll.is_interface.MakeConnectionEdge(
                [sense_filters[i], SenseFilter.sense_input],
                [sense_inputs[i]],
            )
            for i in range(NUM_CELLS)
        ]
        # Connect cell inputs to balance filters
        + [
            fabll.is_interface.MakeConnectionEdge(
                [cell_inputs[i]],
                [balance_filters[i], BalanceFilter.cell_power],
            )
            for i in range(NUM_CELLS)
        ]
        # Connect balance filter outputs to balance inputs
        + [
            fabll.is_interface.MakeConnectionEdge(
                [balance_filters[i], BalanceFilter.balance_input],
                [balance_inputs[i]],
            )
            for i in range(NUM_CELLS)
        ]
        # Chain: balance_filters[i].cap_bridge_connect ~ balance_filters[i-1].balance_input.p
        + [
            fabll.is_interface.MakeConnectionEdge(
                [balance_filters[i], BalanceFilter.cap_bridge_connect],
                [
                    balance_filters[i - 1],
                    BalanceFilter.balance_input,
                    F.DifferentialPair.p,
                ],
            )
            for i in range(1, NUM_CELLS)
        ]
        # Chain: cell_inputs[i].lv ~ cell_inputs[i-1].hv
        + [
            fabll.is_interface.MakeConnectionEdge(
                [cell_inputs[i], F.ElectricPower.lv],
                [cell_inputs[i - 1], F.ElectricPower.hv],
            )
            for i in range(1, NUM_CELLS)
        ]
        # Bottom cell (idx=0): balance_filters[0].cap_bridge_connect.line ~ cell_inputs[0].lv
        + [
            fabll.is_interface.MakeConnectionEdge(
                [
                    balance_filters[0],
                    BalanceFilter.cap_bridge_connect,
                    F.ElectricSignal.line,
                ],
                [cell_inputs[0], F.ElectricPower.lv],
            ),
        ]
        # Bottom sense filter connections
        + [
            fabll.is_interface.MakeConnectionEdge(
                [bottom_sense_filter, SenseFilter.cell_power, F.ElectricPower.hv],
                [cell_inputs[0], F.ElectricPower.lv],
            ),
            fabll.is_interface.MakeConnectionEdge(
                [
                    bottom_sense_filter,
                    SenseFilter.sense_input,
                    F.DifferentialPair.p,
                    F.ElectricSignal.line,
                ],
                [sense_inputs[0], F.DifferentialPair.n, F.ElectricSignal.line],
            ),
            fabll.is_interface.MakeConnectionEdge(
                [
                    bottom_sense_filter,
                    SenseFilter.sense_input,
                    F.DifferentialPair.n,
                    F.ElectricSignal.line,
                ],
                [cell_inputs[0], F.ElectricPower.lv],
            ),
        ]
    )


class ADBMS6830InputFilters(fabll.Node):
    """
    Filters between cell connections and sense/balance pins of the ADBMS6830.
    Hardcoded for 16 cells / 16 channels (no depopulated channels).

    Sense Filters: 200 ohm +/- 1% / 10nF +/- 20% RC low-pass
    Balance Filters: calculated from 100mA max balance current
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # External interfaces
    cell_inputs = [F.ElectricPower.MakeChild() for _ in range(NUM_CELLS)]
    sense_inputs = [F.DifferentialPair.MakeChild() for _ in range(NUM_CELLS)]
    balance_inputs = [F.DifferentialPair.MakeChild() for _ in range(NUM_CELLS)]

    # Internal filter modules
    sense_filters = [SenseFilter.MakeChild() for _ in range(NUM_CELLS)]
    balance_filters = [BalanceFilter.MakeChild() for _ in range(NUM_CELLS)]

    # Bottom sense filter for connecting bottom of stack to lowest ADC channel
    bottom_sense_filter = SenseFilter.MakeChild()

    # ----------------------------------------
    #            Connections
    # ----------------------------------------
    _connections = _build_input_filter_connections(
        cell_inputs, sense_inputs, balance_inputs,
        sense_filters, balance_filters, bottom_sense_filter,
    )
