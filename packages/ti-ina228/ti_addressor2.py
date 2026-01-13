# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
"""
TI INA228 specialized I2C addressor.

The INA228 has a unique 4-bit address selection scheme where each of the
two address pins (A0, A1) can be connected to one of four signals:
- 0: GND (device ground)
- 1: VS (device supply)
- 2: SDA (I2C data line)
- 3: SCL (I2C clock line)

This gives 16 possible addresses (0x40 to 0x4F) based on the formula:
    address = 0x40 + (A1_config * 4) + A0_config

Where A0_config and A1_config are 0-3 based on the signal connected.
"""

import logging

import faebryk.core.node as fabll
import faebryk.library._F as F

logger = logging.getLogger(__name__)


def _build_ti_addressor2() -> type[fabll.Node]:
    """
    Build the TIAddressor2 class with interface fields.

    Done as a function to allow use as base class in ato inheritance.
    """

    class _TIAddressor2(fabll.Node):
        """
        TI INA228 specialized I2C addressor.

        The INA228 uses a 4-signal address selection scheme where A0 and A1
        can each be connected to GND, VS, SDA, or SCL for 16 total addresses.

        Example usage in ato:
            addressor = new TIAddressor2
            addressor.base = 0x40
            addressor.i2c ~ i2c
            assert addressor.address is i2c.address
            addressor.address_line_a0.line ~ package.A0
            addressor.address_line_a0.reference ~ power
            addressor.address_line_a1.line ~ package.A1
            addressor.address_line_a1.reference ~ power
        """

        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

        # Parameters for address calculation
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
        num_addresses = F.Parameters.NumericParameter.MakeChild(
            unit=F.Units.Dimensionless,
            domain=F.NumberDomain.Args(negative=False, integer=True),
        )

        # Address line interfaces
        address_line_a0 = F.ElectricLogic.MakeChild()
        address_line_a1 = F.ElectricLogic.MakeChild()

        # I2C interface for address line to SDA/SCL connections
        i2c = F.I2C.MakeChild()

        # Single electric reference trait
        _single_electric_reference = fabll.Traits.MakeEdge(
            F.has_single_electric_reference.MakeChild()
        )

        # Design check for address line configuration
        design_check = fabll.Traits.MakeEdge(F.implements_design_check.MakeChild())

        class OffsetNotResolvedError(F.implements_design_check.UnfulfilledCheckException):
            """Raised when the offset parameter is not resolved to a single value."""

            def __init__(self, addressor: "_TIAddressor2"):
                super().__init__(
                    "TIAddressor2 offset must be constrained to a single value "
                    "between 0-15. Set i2c.address to determine address configuration.",
                    nodes=[addressor],
                )

        @F.implements_design_check.register_post_design_check
        def __check_post_design__(self):
            """
            Configure address lines based on the solved offset value.

            After the solver determines the offset (from address = base + offset),
            this check connects A0 and A1 to the appropriate signals.
            """
            from faebryk.core.solver.defaultsolver import DefaultSolver
            from faebryk.core.solver.nullsolver import NullSolver

            # Get the address and base parameters and compute offset
            address_lit = self.address.get().try_extract_aliased_literal()
            base_lit = self.base.get().try_extract_aliased_literal()

            if address_lit is None or base_lit is None:
                # Try using solver
                solver = self.design_check.get().get_solver()

                if isinstance(solver, NullSolver):
                    logger.warning(
                        "Solver is NullSolver, can't deduce TIAddressor2 offset"
                    )
                    return

                assert isinstance(solver, DefaultSolver)

                # Try to get address and base from solver
                addr_param = self.address.get().is_parameter.get()
                base_param = self.base.get().is_parameter.get()

                solver.update_superset_cache(self.address.get().can_be_operand.get())
                solver.update_superset_cache(self.base.get().can_be_operand.get())

                addr_lit = solver.inspect_get_known_supersets(addr_param)
                base_lit_solver = solver.inspect_get_known_supersets(base_param)

                if addr_lit is None or not addr_lit.is_singleton():
                    # Offset not yet constrained - this is expected when the user
                    # hasn't specified the I2C address. The address line connection
                    # will be made later when the offset is known.
                    logger.warning(
                        "TIAddressor2 offset not resolved - address line connection "
                        "skipped. Constrain the I2C address to enable automatic "
                        "connection of A0/A1 pins."
                    )
                    return
                if base_lit_solver is None or not base_lit_solver.is_singleton():
                    logger.warning(
                        "TIAddressor2 base not resolved - address line connection "
                        "skipped. Set addressor.base to enable automatic connection "
                        "of A0/A1 pins."
                    )
                    return

                address_val = int(addr_lit.get_single())
                base_val = int(base_lit_solver.get_single())
            else:
                if not address_lit.is_literal.get().is_singleton():
                    logger.warning(
                        "TIAddressor2 address not a singleton - address line "
                        "connection skipped. Constrain the I2C address to a "
                        "specific value."
                    )
                    return
                if not base_lit.is_literal.get().is_singleton():
                    logger.warning(
                        "TIAddressor2 base not a singleton - address line "
                        "connection skipped. Set addressor.base to a specific value."
                    )
                    return
                address_val = int(address_lit.get_single())
                base_val = int(base_lit.get_single())

            # Compute offset
            offset = address_val - base_val

            if offset < 0 or offset > 15:
                raise ValueError(
                    f"TIAddressor2 offset must be 0-15, got {offset}"
                )

            # Decode offset into A0 and A1 configurations
            # offset = (A1_config * 4) + A0_config
            a0_config = offset & 0x3  # Lower 2 bits
            a1_config = (offset >> 2) & 0x3  # Upper 2 bits

            # Map config values to destinations
            # 0: GND (lv), 1: VS (hv), 2: SDA, 3: SCL
            a0_ref = self.address_line_a0.get().reference.get()
            a1_ref = self.address_line_a1.get().reference.get()
            i2c = self.i2c.get()

            a0_destinations = [
                a0_ref.lv.get(),    # GND
                a0_ref.hv.get(),    # VS
                i2c.sda.get().line.get(),   # SDA
                i2c.scl.get().line.get(),   # SCL
            ]

            a1_destinations = [
                a1_ref.lv.get(),    # GND
                a1_ref.hv.get(),    # VS
                i2c.sda.get().line.get(),   # SDA
                i2c.scl.get().line.get(),   # SCL
            ]

            # Connect A0 and A1 to their respective destinations
            a0_line = self.address_line_a0.get().line.get()
            a1_line = self.address_line_a1.get().line.get()

            logger.info(
                f"TIAddressor2: offset={offset}, A0_config={a0_config}, A1_config={a1_config}"
            )

            a0_line.connect(a0_destinations[a0_config])
            a1_line.connect(a1_destinations[a1_config])

        usage_example = fabll.Traits.MakeEdge(
            F.has_usage_example.MakeChild(
                example="""
            from "ti_addressor2.py" import TIAddressor2

            addressor = new TIAddressor2
            addressor.base = 0x40
            addressor.i2c ~ i2c
            assert addressor.address is i2c.address
            addressor.address_line_a0.line ~ package.A0
            addressor.address_line_a0.reference ~ power
            addressor.address_line_a1.line ~ package.A1
            addressor.address_line_a1.reference ~ power
            """,
                language=F.has_usage_example.Language.ato,
            ).put_on_type()
        )

    # Rename for cleaner display
    _TIAddressor2._rename_type("TIAddressor2")

    return _TIAddressor2


# Build and export the class at module import time
TIAddressor2 = _build_ti_addressor2()
