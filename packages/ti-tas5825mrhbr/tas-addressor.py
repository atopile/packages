# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
TAS5825MRHBR I2C address configuration module.

The TAS5825M uses a single address pin (ADR) with a resistor to GND to select
one of 4 I2C addresses. The resistor value determines the offset:

- 0 ohm    → offset 0
- 1 kohm   → offset 1
- 4.7 kohm → offset 2
- 15 kohm  → offset 3

Final address = base + offset (base = 0x4C from datasheet)
"""

import logging

import faebryk.core.node as fabll
import faebryk.library._F as F

logger = logging.getLogger(__name__)

# Resistor values for each offset (index = offset)
RESISTANCE_MAP = [
    (0.0, 0.0),         # offset 0: 0 ohm (short)
    (900.0, 1100.0),    # offset 1: 1 kohm +/- 10%
    (4230.0, 5170.0),   # offset 2: 4.7 kohm +/- 10%
    (13500.0, 16500.0), # offset 3: 15 kohm +/- 10%
]


class TAS_addressor(fabll.Node):
    """
    Configures TAS5825M I2C address via a resistor on the ADR pin.

    The TAS5825M has 4 possible I2C addresses selected by a resistor
    from the ADR pin to GND. After the solver resolves the offset value,
    the addr_resistor resistance is constrained to the corresponding value.

    Final address = base + offset

    Example usage in ato:
        addressor = new TAS_addressor
        addressor.base = 0x4C
        assert addressor.address is i2c.address
        addressor.address_line.line ~ device.ADR
        addressor.address_line.reference ~ power
    """

    # ----------------------------------------
    #     parameters
    # ----------------------------------------
    address = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Dimensionless,
        domain=F.NumberDomain.Args(negative=False, integer=True),
    )
    offset = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Dimensionless,
        domain=F.NumberDomain.Args(negative=False, integer=True),
    )
    base = F.Parameters.NumericParameter.MakeChild(
        unit=F.Units.Dimensionless,
        domain=F.NumberDomain.Args(negative=False, integer=True),
    )

    # ----------------------------------------
    #     interfaces / children
    # ----------------------------------------
    address_line = F.ElectricLogic.MakeChild()
    addr_resistor = F.Resistor.MakeChild()

    # ----------------------------------------
    #     traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _single_electric_reference = fabll.Traits.MakeEdge(
        F.has_single_electric_reference.MakeChild()
    )
    # Note: NOT using _has_part_removed since this module contains a physical Resistor child

    # Design check trait for post-solve resistor configuration
    design_check = fabll.Traits.MakeEdge(F.implements_design_check.MakeChild())

    # ----------------------------------------
    #     equations (class-level constraints)
    # ----------------------------------------
    # offset is! address - base
    _addr_minus_base = F.Expressions.Subtract.MakeChild([address], [base])
    _offset_eq = F.Expressions.Is.MakeChild(
        [offset], [_addr_minus_base], assert_=True
    )

    # address is! base + offset
    _base_plus_offset = F.Expressions.Add.MakeChild([base], [offset])
    _address_eq = F.Expressions.Is.MakeChild(
        [address], [_base_plus_offset], assert_=True
    )

    # Constrain offset to [0, 3]
    _offset_range = F.Literals.Numbers.MakeChild(
        min=0, max=3, unit=F.Units.Dimensionless
    )
    _offset_constraint = F.Expressions.IsSubset.MakeChild(
        [offset], [_offset_range], assert_=True
    )

    # ----------------------------------------
    #     post-solve check
    # ----------------------------------------
    class OffsetNotResolvedError(F.implements_design_check.UnfulfilledCheckException):
        """Raised when the offset parameter cannot be resolved to a single value."""

        def __init__(self, addressor: "TAS_addressor"):
            super().__init__(
                "TAS_addressor offset must be constrained to a single value (0-3).",
                nodes=[addressor],
            )

    @F.implements_design_check.register_post_instantiation_setup_check
    def __check_post_instantiation_setup__(self):
        """
        Set addr_resistor resistance based on the solved offset value.

        After the solver resolves the offset (0-3), this method constrains
        the resistor to the corresponding value from the TAS5825M datasheet.
        """
        solver = self.design_check.get().get_solver()

        offset_p = self.offset.get().is_parameter.get()
        logger.debug(f"Running solver for TAS_addressor: {self}")

        # Try to extract offset
        lit = solver.extract_superset(offset_p)

        if lit is None or not lit.op_setic_is_singleton():
            lit = solver.simplify_and_extract_superset(offset_p)

        # Fallback to direct extraction
        if lit is None or not lit.op_setic_is_singleton():
            direct_lit = self.offset.get().try_extract_superset()
            if direct_lit is not None and direct_lit.is_singleton():
                lit = direct_lit.is_literal.get()

        if lit is None or not lit.op_setic_is_singleton():
            logger.warning(
                "TAS_addressor offset not resolved - resistor value not set. "
                "Constrain the I2C address or offset to enable automatic "
                "resistor selection."
            )
            return

        # Extract offset value
        lit_node = fabll.Traits(lit).get_obj_raw()
        offset = int(lit_node.cast(F.Literals.Numbers).get_single())

        if not 0 <= offset <= 3:
            raise ValueError(
                f"TAS_addressor offset {offset} out of range [0, 3]"
            )

        if offset == 0:
            # Offset 0 means ADR is shorted to GND (no resistor needed)
            # Remove the resistor part from the design
            fabll.Traits.create_and_add_instance_to(
                self.addr_resistor.get(), F.has_part_removed
            )
            logger.debug("TAS_addressor: offset=0, resistor removed (short to GND)")
        else:
            # Get the resistance range for this offset
            r_min, r_max = RESISTANCE_MAP[offset]

            # Constrain the resistor's resistance
            resistance_param = self.addr_resistor.get().resistance.get()
            g = resistance_param.g
            tg = resistance_param.tg
            unit = resistance_param.try_get_units()

            lit = (
                F.Literals.Numbers.create_instance(g=g, tg=tg)
                .setup_from_min_max(min=r_min, max=r_max, unit=unit)
            )
            resistance_param.set_superset(g, lit)

            logger.debug(
                f"TAS_addressor: Set resistor to {r_min}-{r_max} ohm "
                f"for offset={offset}"
            )

    # ----------------------------------------
    #     usage example
    # ----------------------------------------
    usage_example = fabll.Traits.MakeEdge(
        F.has_usage_example.MakeChild(
            example="""
        import TAS_addressor
        import I2C
        import ElectricPower

        i2c = new I2C
        power = new ElectricPower

        addressor = new TAS_addressor
        addressor.base = 0x4C  # TAS5825M base address

        assert addressor.address is i2c.address
        addressor.address_line.line ~ device.ADR
        addressor.address_line.reference ~ power
        """,
            language=F.has_usage_example.Language.ato,
        ).put_on_type()
    )
