# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import math

import faebryk.core.node as fabll
import faebryk.library._F as F


class SenseFilter(fabll.Node):
    """
    RC filter for cell voltage sensing.
    Exposes sub-components for external wiring.
    """

    cell_power = F.ElectricPower.MakeChild()
    sense_input = F.DifferentialPair.MakeChild()
    sense_filter = F.FilterElectricalRC.MakeChild()

    sense_filter_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    sense_filter_capacitance = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Farad
    )

    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Note: Equations linking parameters to filter components will be handled
    # at the parent level or in .ato file to avoid path resolution issues


class BalanceFilter(fabll.Node):
    """
    Dual RC filter for cell balancing.
    Exposes sub-components for external wiring.
    """

    cell_power = F.ElectricPower.MakeChild()
    balance_input = F.DifferentialPair.MakeChild()
    cap_bridge_connect = F.ElectricSignal.MakeChild()

    top_balance_filter = F.FilterElectricalRC.MakeChild()
    bottom_balance_filter = F.FilterElectricalRC.MakeChild()

    bleed_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    bleed_filter_capacitance = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Farad
    )

    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Note: Equations linking parameters to filter components will be handled
    # at the parent level or in .ato file to avoid path resolution issues


class ADBMS6830InputFilters(fabll.Node):
    """
    Filters between the cell connections and the ADBMS6830.
    """

    sense_filter_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    sense_filter_capacitance = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Farad
    )
    max_balance_current = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ampere)
    bleed_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    bleed_filter_capacitance = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Farad
    )

    NUMBER_OF_CHANNELS = 16

    cell_inputs = [F.ElectricPower.MakeChild() for _ in range(NUMBER_OF_CHANNELS)]
    sense_inputs = [F.DifferentialPair.MakeChild() for _ in range(NUMBER_OF_CHANNELS)]
    balance_inputs = [F.DifferentialPair.MakeChild() for _ in range(NUMBER_OF_CHANNELS)]

    # Try a single custom class child first to test
    test_sense_filter = SenseFilter.MakeChild()

    depop_resistor = F.Resistor.MakeChild()

    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Note: Equations temporarily removed to isolate the issue
