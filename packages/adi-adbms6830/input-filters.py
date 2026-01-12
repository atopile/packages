# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
ADBMS6830 Input Filters Module

This module implements the input filter circuitry for the ADI ADBMS6830 battery
cell monitoring IC. It includes:
- SenseFilter: RC filter for cell voltage sensing
- BalanceFilter: Dual RC filter for cell balancing with transient protection
- ADBMS6830InputFilters: Factory module that creates arrays of filters for N cells

The filters are designed to:
1. Protect ADC inputs from high-frequency noise
2. Provide current-limiting for balancing
3. Handle depopulated channels (unused cell inputs)
"""

import logging
import math
from typing import Self, cast

import faebryk.core.faebrykpy as fbrk
import faebryk.core.node as fabll
import faebryk.library._F as F
from faebryk.core import graph
from faebryk.libs.util import once

logger = logging.getLogger(__name__)


class SenseFilter(fabll.Node):
    """
    RC filter for cell voltage sensing.

    Connects cell_power.hv through a resistor to sense_input.p.line,
    with a capacitor from sense_input.p.line to sense_input.n.line.

    This creates a low-pass filter to protect the ADC input from noise.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    cell_power = F.ElectricPower.MakeChild()
    sense_input = F.DifferentialPair.MakeChild()
    filter = F.FilterElectricalRC.MakeChild()

    # Parameters for configurability
    filter_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    filter_capacitance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Farad)

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _single_electric_reference = fabll.Traits.MakeEdge(
        F.has_single_electric_reference.MakeChild()
    )

    # ----------------------------------------
    #             connections
    # ----------------------------------------
    # cell_power.hv -> resistor -> sense_input.p.line
    _hv_to_resistor = fabll.MakeEdge(
        [cell_power, "hv"],
        [filter, "resistor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _resistor_to_sense_p = fabll.MakeEdge(
        [filter, "resistor", "unnamed[1]"],
        [sense_input, "p", "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    # sense_input.p.line -> capacitor -> sense_input.n.line
    _sense_p_to_cap = fabll.MakeEdge(
        [sense_input, "p", "line"],
        [filter, "capacitor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _cap_to_sense_n = fabll.MakeEdge(
        [filter, "capacitor", "unnamed[1]"],
        [sense_input, "n", "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    @classmethod
    def MakeChild(  # type: ignore[override]
        cls,
        resistance_ohms: float = 200.0,
        resistance_tolerance: float = 0.01,
        capacitance_nF: float = 10.0,
        capacitance_tolerance: float = 0.2,
    ) -> fabll._ChildField[Self]:
        """
        Create a SenseFilter with configurable component values.

        Args:
            resistance_ohms: Filter resistance in ohms (default 200)
            resistance_tolerance: Relative tolerance (default 1%)
            capacitance_nF: Filter capacitance in nanofarads (default 10)
            capacitance_tolerance: Relative tolerance (default 20%)
        """
        out = fabll._ChildField(cls)

        # Constrain resistance
        resistance_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.filter, "resistor", "resistance"],
            min=resistance_ohms * (1 - resistance_tolerance),
            max=resistance_ohms * (1 + resistance_tolerance),
            unit=F.Units.Ohm,
        )
        out.add_dependant(resistance_constraint)

        # Constrain capacitance
        capacitance_F = capacitance_nF * 1e-9
        capacitance_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.filter, "capacitor", "capacitance"],
            min=capacitance_F * (1 - capacitance_tolerance),
            max=capacitance_F * (1 + capacitance_tolerance),
            unit=F.Units.Farad,
        )
        out.add_dependant(capacitance_constraint)

        return out


class BalanceFilter(fabll.Node):
    """
    Dual RC filter for cell balancing with transient protection.

    Creates two RC filters:
    - Top filter: cell_power.hv -> resistor -> balance_input.p.line
    - Bottom filter: cell_power.lv -> resistor -> balance_input.n.line

    Plus capacitors for transient filtering:
    - balance_input.p.line -> cap -> balance_input.n.line
    - balance_input.n.line -> cap -> cap_bridge_connect (to cell below)
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    cell_power = F.ElectricPower.MakeChild()
    balance_input = F.DifferentialPair.MakeChild()
    cap_bridge_connect = F.ElectricSignal.MakeChild()

    # Two RC filters for top and bottom of the balance network
    top_filter = F.FilterElectricalRC.MakeChild()
    bottom_filter = F.FilterElectricalRC.MakeChild()

    # Parameters
    bleed_resistance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ohm)
    filter_capacitance = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Farad)

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _single_electric_reference = fabll.Traits.MakeEdge(
        F.has_single_electric_reference.MakeChild()
    )

    # ----------------------------------------
    #             connections
    # ----------------------------------------
    # Top: cell_power.hv -> top_resistor -> balance_input.p.line
    _hv_to_top_resistor = fabll.MakeEdge(
        [cell_power, "hv"],
        [top_filter, "resistor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _top_resistor_to_balance_p = fabll.MakeEdge(
        [top_filter, "resistor", "unnamed[1]"],
        [balance_input, "p", "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    # Bottom: cell_power.lv -> bottom_resistor -> balance_input.n.line
    _lv_to_bottom_resistor = fabll.MakeEdge(
        [cell_power, "lv"],
        [bottom_filter, "resistor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _bottom_resistor_to_balance_n = fabll.MakeEdge(
        [bottom_filter, "resistor", "unnamed[1]"],
        [balance_input, "n", "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    # Capacitor: balance_input.p.line -> cap -> balance_input.n.line
    _balance_p_to_top_cap = fabll.MakeEdge(
        [balance_input, "p", "line"],
        [top_filter, "capacitor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _top_cap_to_balance_n = fabll.MakeEdge(
        [top_filter, "capacitor", "unnamed[1]"],
        [balance_input, "n", "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    # Bridge cap: balance_input.n.line -> cap -> cap_bridge_connect.line
    _balance_n_to_bottom_cap = fabll.MakeEdge(
        [balance_input, "n", "line"],
        [bottom_filter, "capacitor", "unnamed[0]"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )
    _bottom_cap_to_bridge = fabll.MakeEdge(
        [bottom_filter, "capacitor", "unnamed[1]"],
        [cap_bridge_connect, "line"],
        edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
    )

    @classmethod
    def MakeChild(  # type: ignore[override]
        cls,
        bleed_resistance_ohms: float = 20.0,
        bleed_resistance_tolerance: float = 0.05,
        capacitance_nF: float = 10.0,
        capacitance_tolerance: float = 0.2,
    ) -> fabll._ChildField[Self]:
        """
        Create a BalanceFilter with configurable component values.

        Args:
            bleed_resistance_ohms: Bleed resistance in ohms (default 20)
            bleed_resistance_tolerance: Relative tolerance (default 5%)
            capacitance_nF: Filter capacitance in nanofarads (default 10)
            capacitance_tolerance: Relative tolerance (default 20%)
        """
        out = fabll._ChildField(cls)

        # Constrain top resistor
        top_res_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.top_filter, "resistor", "resistance"],
            min=bleed_resistance_ohms * (1 - bleed_resistance_tolerance),
            max=bleed_resistance_ohms * (1 + bleed_resistance_tolerance),
            unit=F.Units.Ohm,
        )
        out.add_dependant(top_res_constraint)

        # Constrain bottom resistor
        bottom_res_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.bottom_filter, "resistor", "resistance"],
            min=bleed_resistance_ohms * (1 - bleed_resistance_tolerance),
            max=bleed_resistance_ohms * (1 + bleed_resistance_tolerance),
            unit=F.Units.Ohm,
        )
        out.add_dependant(bottom_res_constraint)

        # Constrain capacitances
        capacitance_F = capacitance_nF * 1e-9
        top_cap_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.top_filter, "capacitor", "capacitance"],
            min=capacitance_F * (1 - capacitance_tolerance),
            max=capacitance_F * (1 + capacitance_tolerance),
            unit=F.Units.Farad,
        )
        out.add_dependant(top_cap_constraint)

        bottom_cap_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
            param_ref=[out, cls.bottom_filter, "capacitor", "capacitance"],
            min=capacitance_F * (1 - capacitance_tolerance),
            max=capacitance_F * (1 + capacitance_tolerance),
            unit=F.Units.Farad,
        )
        out.add_dependant(bottom_cap_constraint)

        # Power constraint for resistors: max_power >= (4.25/2)^2 / R
        # At max cell voltage of 4.25V, each resistor sees half the voltage
        max_cell_voltage = 4.25
        half_voltage = max_cell_voltage / 2
        min_power = (half_voltage * half_voltage) / bleed_resistance_ohms

        # Create literal for min power requirement
        top_power_lit = F.Literals.Numbers.MakeChild(
            min=min_power, max=min_power, unit=F.Units.Watt
        )
        out.add_dependant(top_power_lit)

        top_power_constraint = F.Expressions.GreaterOrEqual.MakeChild(
            [out, cls.top_filter, "resistor", "max_power"],
            [top_power_lit],
            assert_=True,
        )
        out.add_dependant(top_power_constraint)

        bottom_power_lit = F.Literals.Numbers.MakeChild(
            min=min_power, max=min_power, unit=F.Units.Watt
        )
        out.add_dependant(bottom_power_lit)

        bottom_power_constraint = F.Expressions.GreaterOrEqual.MakeChild(
            [out, cls.bottom_filter, "resistor", "max_power"],
            [bottom_power_lit],
            assert_=True,
        )
        out.add_dependant(bottom_power_constraint)

        return out


class ADBMS6830InputFilters(fabll.Node):
    """
    Input filter bank for ADBMS6830 battery cell monitoring IC.

    Creates arrays of sense and balance filters for N cells, plus handles:
    - Bottom-of-stack sense filter
    - Depopulated channel connections (unused channels tied to top of stack)
    - Cell stack interconnections

    Parameters (from ato template):
        number_of_cells: Number of battery cells (default 6)
        sense_filter_resistance_ohms: Sense filter R value (default 200)
        sense_filter_capacitance_nF: Sense filter C value (default 10)
        max_balance_current_mA: Maximum balance current (default 200)
        total_number_of_channels: Total ADC channels (default 16)
    """

    # Base class attributes that will be populated by factory()
    # PointerSequences for iteration in ato
    cell_inputs = F.Collections.PointerSequence.MakeChild()
    sense_inputs = F.Collections.PointerSequence.MakeChild()
    balance_inputs = F.Collections.PointerSequence.MakeChild()
    sense_filters = F.Collections.PointerSequence.MakeChild()
    balance_filters = F.Collections.PointerSequence.MakeChild()

    # Bottom sense filter (always created)
    bottom_sense_filter = SenseFilter.MakeChild()

    # Depop resistor (may be unused if no depopulated channels)
    depop_resistor = F.Resistor.MakeChild()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Mark as abstract since factory creates concrete implementations
    is_abstract = fabll.Traits.MakeEdge(fabll.is_abstract.MakeChild()).put_on_type()

    @classmethod
    @once
    def factory(
        cls,
        number_of_cells: int,
        sense_filter_resistance_ohms: float,
        sense_filter_capacitance_nF: float,
        max_balance_current_mA: float,
        total_number_of_channels: int,
    ) -> type[Self]:
        """
        Create a concrete ADBMS6830InputFilters type with the specified configuration.

        This factory creates:
        1. Arrays of ElectricPower (cell_inputs) and DifferentialPair (sense/balance_inputs)
        2. Arrays of SenseFilter and BalanceFilter
        3. All internal connections between filters and interfaces
        4. Bottom sense filter for stack ground
        5. Depopulated channel handling
        """
        if number_of_cells <= 0:
            raise ValueError("At least one cell is required")
        if number_of_cells > total_number_of_channels:
            raise ValueError("number_of_cells cannot exceed total_number_of_channels")

        # Calculate bleed resistance from max balance current
        # R = V / I, with V = 4.25V (max cell voltage) and I split between two resistors
        max_cell_voltage = 4.25
        bleed_resistance_target = (
            max_cell_voltage / (max_balance_current_mA / 1000)
        ) / 2

        # Calculate filter capacitance from corner frequency
        # Datasheet recommends ~80kHz corner for balance filters
        corner_freq_hz = 80000
        bleed_filter_capacitance_nF = (
            1 / (bleed_resistance_target * 2 * math.pi * corner_freq_hz)
        ) * 1e9

        type_name = (
            f"ADBMS6830InputFilters<"
            f"number_of_cells={number_of_cells},"
            f"sense_filter_resistance_ohms={sense_filter_resistance_ohms},"
            f"sense_filter_capacitance_nF={sense_filter_capacitance_nF},"
            f"max_balance_current_mA={max_balance_current_mA},"
            f"total_number_of_channels={total_number_of_channels}>"
        )

        ConcreteFilters = fabll.Node._copy_type(cls, name=type_name)

        # Create cell_inputs array (ElectricPower)
        for i in range(number_of_cells):
            cell_input = F.ElectricPower.MakeChild()
            ConcreteFilters._handle_cls_attr(f"cell_inputs[{i}]", cell_input)
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.cell_inputs],
                elem_ref=[cell_input],
                index=i,
            )
            ConcreteFilters._handle_cls_attr(f"_cell_input_link_{i}", edge)

        # Create sense_inputs array (DifferentialPair) - for total channels
        for i in range(total_number_of_channels):
            sense_input = F.DifferentialPair.MakeChild()
            ConcreteFilters._handle_cls_attr(f"sense_inputs[{i}]", sense_input)
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.sense_inputs],
                elem_ref=[sense_input],
                index=i,
            )
            ConcreteFilters._handle_cls_attr(f"_sense_input_link_{i}", edge)

        # Create balance_inputs array (DifferentialPair) - for total channels
        for i in range(total_number_of_channels):
            balance_input = F.DifferentialPair.MakeChild()
            ConcreteFilters._handle_cls_attr(f"balance_inputs[{i}]", balance_input)
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.balance_inputs],
                elem_ref=[balance_input],
                index=i,
            )
            ConcreteFilters._handle_cls_attr(f"_balance_input_link_{i}", edge)

        # Create sense_filters array
        for i in range(number_of_cells):
            sense_filter = SenseFilter.MakeChild(
                resistance_ohms=sense_filter_resistance_ohms,
                resistance_tolerance=0.01,
                capacitance_nF=sense_filter_capacitance_nF,
                capacitance_tolerance=0.2,
            )
            ConcreteFilters._handle_cls_attr(f"sense_filters[{i}]", sense_filter)
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.sense_filters],
                elem_ref=[sense_filter],
                index=i,
            )
            ConcreteFilters._handle_cls_attr(f"_sense_filter_link_{i}", edge)

            # Connect cell_inputs[i] ~ sense_filters[i].cell_power
            conn = fabll.MakeEdge(
                [f"cell_inputs[{i}]"],  # type: ignore[list-item]
                [sense_filter, "cell_power"],
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr(f"_sense_cell_conn_{i}", conn)

            # Connect sense_filters[i].sense_input ~ sense_inputs[i]
            conn2 = fabll.MakeEdge(
                [sense_filter, "sense_input"],
                [f"sense_inputs[{i}]"],  # type: ignore[list-item]
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr(f"_sense_out_conn_{i}", conn2)

        # Create balance_filters array
        for i in range(number_of_cells):
            balance_filter = BalanceFilter.MakeChild(
                bleed_resistance_ohms=bleed_resistance_target,
                bleed_resistance_tolerance=0.05,
                capacitance_nF=bleed_filter_capacitance_nF,
                capacitance_tolerance=0.2,
            )
            ConcreteFilters._handle_cls_attr(f"balance_filters[{i}]", balance_filter)
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.balance_filters],
                elem_ref=[balance_filter],
                index=i,
            )
            ConcreteFilters._handle_cls_attr(f"_balance_filter_link_{i}", edge)

            # Connect cell_inputs[i] ~ balance_filters[i].cell_power
            conn = fabll.MakeEdge(
                [f"cell_inputs[{i}]"],  # type: ignore[list-item]
                [balance_filter, "cell_power"],
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr(f"_balance_cell_conn_{i}", conn)

            # Connect balance_filters[i].balance_input ~ balance_inputs[i]
            conn2 = fabll.MakeEdge(
                [balance_filter, "balance_input"],
                [f"balance_inputs[{i}]"],  # type: ignore[list-item]
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr(f"_balance_out_conn_{i}", conn2)

            # Connect cap_bridge_connect
            if i > 0:
                # Connect to cell below's balance_input.p
                bridge_conn = fabll.MakeEdge(
                    [balance_filter, "cap_bridge_connect"],
                    [f"balance_filters[{i - 1}]", "balance_input", "p"],  # type: ignore[list-item]
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
                ConcreteFilters._handle_cls_attr(f"_bridge_conn_{i}", bridge_conn)

        # Connect first balance filter's bridge to cell_inputs[0].lv (ground)
        if number_of_cells > 0:
            first_bridge_conn = fabll.MakeEdge(
                ["balance_filters[0]", "cap_bridge_connect", "line"],
                ["cell_inputs[0]", "lv"],
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr("_first_bridge_to_gnd", first_bridge_conn)

        # Connect cell stack (cell_inputs[i].lv ~ cell_inputs[i-1].hv)
        for i in range(1, number_of_cells):
            stack_conn = fabll.MakeEdge(
                [f"cell_inputs[{i}]", "lv"],  # type: ignore[list-item]
                [f"cell_inputs[{i - 1}]", "hv"],  # type: ignore[list-item]
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr(f"_stack_conn_{i}", stack_conn)

        # Note: bottom_sense_filter is defined at class level with default parameters
        # Additional constraints can be added here if needed

        # Connect bottom sense filter
        # bottom_sense_filter.cell_power.hv ~ cell_inputs[0].lv
        bottom_cell_conn = fabll.MakeEdge(
            [cls.bottom_sense_filter, "cell_power", "hv"],
            ["cell_inputs[0]", "lv"],
            edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
        )
        ConcreteFilters._handle_cls_attr("_bottom_sense_cell_conn", bottom_cell_conn)

        # bottom_sense_filter.sense_input.p.line ~ sense_inputs[0].n.line
        bottom_p_conn = fabll.MakeEdge(
            [cls.bottom_sense_filter, "sense_input", "p", "line"],
            ["sense_inputs[0]", "n", "line"],
            edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
        )
        ConcreteFilters._handle_cls_attr("_bottom_sense_p_conn", bottom_p_conn)

        # bottom_sense_filter.sense_input.n.line ~ cell_inputs[0].lv
        bottom_n_conn = fabll.MakeEdge(
            [cls.bottom_sense_filter, "sense_input", "n", "line"],
            ["cell_inputs[0]", "lv"],
            edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
        )
        ConcreteFilters._handle_cls_attr("_bottom_sense_n_conn", bottom_n_conn)

        # Handle depopulated channels
        number_of_depopulated = total_number_of_channels - number_of_cells
        if number_of_depopulated > 0:
            # Configure depop resistor (1kohm ±1%)
            depop_res_constraint = (
                F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
                    param_ref=[cls.depop_resistor, "resistance"],
                    min=1000 * 0.99,
                    max=1000 * 1.01,
                    unit=F.Units.Ohm,
                )
            )
            ConcreteFilters._handle_cls_attr(
                "_depop_res_constraint", depop_res_constraint
            )

            for i in range(number_of_depopulated):
                channel_idx = total_number_of_channels - 1 - i

                # sense_inputs[channel_idx].p.line ~> depop_resistor ~> top.hv
                depop_sense_p_conn = fabll.MakeEdge(
                    [f"sense_inputs[{channel_idx}]", "p", "line"],  # type: ignore[list-item]
                    [cls.depop_resistor, "unnamed[0]"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
                ConcreteFilters._handle_cls_attr(
                    f"_depop_sense_p_{channel_idx}", depop_sense_p_conn
                )

                # sense_inputs[channel_idx].n.line ~> depop_resistor ~> top.hv
                depop_sense_n_conn = fabll.MakeEdge(
                    [f"sense_inputs[{channel_idx}]", "n", "line"],  # type: ignore[list-item]
                    [cls.depop_resistor, "unnamed[0]"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
                ConcreteFilters._handle_cls_attr(
                    f"_depop_sense_n_{channel_idx}", depop_sense_n_conn
                )

                # balance_inputs[channel_idx].p.line ~> depop_resistor ~> top.hv
                depop_bal_p_conn = fabll.MakeEdge(
                    [f"balance_inputs[{channel_idx}]", "p", "line"],  # type: ignore[list-item]
                    [cls.depop_resistor, "unnamed[0]"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
                ConcreteFilters._handle_cls_attr(
                    f"_depop_bal_p_{channel_idx}", depop_bal_p_conn
                )

                # balance_inputs[channel_idx].n.line ~> depop_resistor ~> top.hv
                depop_bal_n_conn = fabll.MakeEdge(
                    [f"balance_inputs[{channel_idx}]", "n", "line"],  # type: ignore[list-item]
                    [cls.depop_resistor, "unnamed[0]"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
                ConcreteFilters._handle_cls_attr(
                    f"_depop_bal_n_{channel_idx}", depop_bal_n_conn
                )

            # Connect depop_resistor.unnamed[1] to top of stack
            depop_to_top_conn = fabll.MakeEdge(
                [cls.depop_resistor, "unnamed[1]"],
                [f"cell_inputs[{number_of_cells - 1}]", "hv"],  # type: ignore[list-item]
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteFilters._handle_cls_attr("_depop_to_top", depop_to_top_conn)

        return ConcreteFilters

    @classmethod
    def MakeChild(  # type: ignore[override]
        cls,
        number_of_cells: int = 6,
        sense_filter_resistance_ohms: float = 200.0,
        sense_filter_capacitance_nF: float = 10.0,
        max_balance_current_mA: float = 200.0,
        total_number_of_channels: int = 16,
    ) -> fabll._ChildField[Self]:
        """
        Create an ADBMS6830InputFilters child field with the specified configuration.

        Args:
            number_of_cells: Number of battery cells (default 6)
            sense_filter_resistance_ohms: Sense filter resistance (default 200)
            sense_filter_capacitance_nF: Sense filter capacitance (default 10)
            max_balance_current_mA: Maximum balance current (default 200)
            total_number_of_channels: Total ADC channels (default 16)
        """
        logger.debug(
            f"ADBMS6830InputFilters.MakeChild called: "
            f"cells={number_of_cells}, channels={total_number_of_channels}"
        )

        ConcreteFilters = cls.factory(
            number_of_cells=number_of_cells,
            sense_filter_resistance_ohms=sense_filter_resistance_ohms,
            sense_filter_capacitance_nF=sense_filter_capacitance_nF,
            max_balance_current_mA=max_balance_current_mA,
            total_number_of_channels=total_number_of_channels,
        )

        return cast(fabll._ChildField[Self], fabll._ChildField(ConcreteFilters))

    usage_example = fabll.Traits.MakeEdge(
        F.has_usage_example.MakeChild(
            example="""
        import ADBMS6830InputFilters, ElectricPower, DifferentialPair

        # Create filter bank for 16 cells
        filters = new ADBMS6830InputFilters<
            number_of_cells=16,
            sense_filter_resistance_ohms=200,
            sense_filter_capacitance_nF=10,
            max_balance_current_mA=100,
            total_number_of_channels=16
        >

        # Connect to external cell stack
        for i in range(16):
            cell_stack[i] ~ filters.cell_inputs[i]

        # Connect to ADBMS6830 sense inputs
        for i in range(16):
            adbms.cell_sense_inputs[i] ~ filters.sense_inputs[i]
            adbms.cell_balance_inputs[i] ~ filters.balance_inputs[i]
        """,
            language=F.has_usage_example.Language.ato,
        ).put_on_type()
    )


# -----------------------------------------------------------------------------
#                                 Tests
# -----------------------------------------------------------------------------


def test_sense_filter_basic():
    """Test basic SenseFilter creation."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        sense_filter = SenseFilter.MakeChild()

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    assert app.sense_filter.get() is not None
    assert app.sense_filter.get().cell_power.get() is not None
    assert app.sense_filter.get().sense_input.get() is not None
    assert app.sense_filter.get().filter.get() is not None


def test_balance_filter_basic():
    """Test basic BalanceFilter creation."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        balance_filter = BalanceFilter.MakeChild()

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    assert app.balance_filter.get() is not None
    assert app.balance_filter.get().cell_power.get() is not None
    assert app.balance_filter.get().balance_input.get() is not None
    assert app.balance_filter.get().top_filter.get() is not None
    assert app.balance_filter.get().bottom_filter.get() is not None


def test_input_filters_factory():
    """Test ADBMS6830InputFilters factory with various cell counts."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        filters = ADBMS6830InputFilters.MakeChild(
            number_of_cells=6,
            sense_filter_resistance_ohms=200,
            sense_filter_capacitance_nF=10,
            max_balance_current_mA=200,
            total_number_of_channels=16,
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    # Check that arrays were created
    cell_inputs = app.filters.get().cell_inputs.get().as_list()
    assert len(cell_inputs) == 6

    sense_inputs = app.filters.get().sense_inputs.get().as_list()
    assert len(sense_inputs) == 16

    balance_inputs = app.filters.get().balance_inputs.get().as_list()
    assert len(balance_inputs) == 16

    sense_filters = app.filters.get().sense_filters.get().as_list()
    assert len(sense_filters) == 6

    balance_filters = app.filters.get().balance_filters.get().as_list()
    assert len(balance_filters) == 6


def test_input_filters_16_cells():
    """Test ADBMS6830InputFilters with full 16 cells (no depopulated channels)."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        filters = ADBMS6830InputFilters.MakeChild(
            number_of_cells=16,
            sense_filter_resistance_ohms=200,
            sense_filter_capacitance_nF=10,
            max_balance_current_mA=100,
            total_number_of_channels=16,
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    cell_inputs = app.filters.get().cell_inputs.get().as_list()
    assert len(cell_inputs) == 16

    sense_filters = app.filters.get().sense_filters.get().as_list()
    assert len(sense_filters) == 16
