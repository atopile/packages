# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import StrEnum
from pathlib import Path
from typing import Self, cast

import faebryk.core.node as fabll
import faebryk.library._F as F
from atopile.errors import UserBadParameterError
from faebryk.libs.util import once

logger = logging.getLogger(__name__)


class NetTie(fabll.Node):
    """
    A net tie component that can bridge different interfaces.

    Net ties are used to connect different nets together on the PCB,
    typically for connecting ground planes or power islands.

    Example usage in ato:
        # Basic 2-pin net tie connecting grounds
        basic_nettie = new NetTie

        # Connect high-voltage side instead of ground
        hv_nettie = new NetTie<connect_gnd=False>

        # 3-pin SMD net tie with 2mm pads
        wide_nettie = new NetTie<width=2.0, pin_count=3>

        # THT net tie
        tht_nettie = new NetTie<width=0.3, pad_type="THT">
    """

    class PadType(StrEnum):
        SMD = "SMD"
        THT = "THT"

    # Mark as abstract - concrete types are created via factory
    is_abstract = fabll.Traits.MakeEdge(fabll.is_abstract.MakeChild()).put_on_type()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Part is removed - net ties don't go through part picking
    _has_part_removed = fabll.Traits.MakeEdge(F.has_part_removed.MakeChild())

    # Can attach to footprint
    _can_attach_to_footprint = fabll.Traits.MakeEdge(
        F.Footprints.can_attach_to_footprint.MakeChild()
    )

    # Designator prefix JP for jumper
    _designator_prefix = fabll.Traits.MakeEdge(
        F.has_designator_prefix.MakeChild(F.has_designator_prefix.Prefix.JP)
    )

    # Design check for footprint registration
    design_check = fabll.Traits.MakeEdge(F.implements_design_check.MakeChild())

    # Footprint file path - set by factory
    _footprint_file_path = F.Parameters.StringParameter.MakeChild()

    # PointerSequence for power interfaces - elements are added dynamically by factory()
    power = F.Collections.PointerSequence.MakeChild()

    usage_example = fabll.Traits.MakeEdge(
        F.has_usage_example.MakeChild(
            example="""
        from "NetTie.py" import NetTie

        # Basic 2-pin net tie (SMD, 0.5mm pad, connects gnd)
        basic_nettie = new NetTie

        # Net tie connecting high-voltage side
        hv_nettie = new NetTie<connect_gnd=False>

        # 3-pin SMD net tie with 2mm pads
        wide_nettie = new NetTie<width=2.0, pin_count=3>

        # THT net tie with 0.3mm pads
        tht_nettie = new NetTie<width=0.3, pad_type="THT">

        # Bridge connect for 2-pin netties
        power_a = new ElectricPower
        power_b = new ElectricPower
        power_a ~> basic_nettie ~> power_b
        """,
            language=F.has_usage_example.Language.ato,
        ).put_on_type()
    )

    @F.implements_design_check.register_post_design_check
    def __check_post_design__(self):
        """Register the footprint library during post-design check."""
        from faebryk.libs.part_lifecycle import PartLifecycle

        # Get footprint path
        fp_path_lit = self._footprint_file_path.get().try_extract_constrained_literal()

        if fp_path_lit is None:
            logger.warning("Footprint path not set for NetTie")
            return

        fp_path_str = fp_path_lit.get_values()[0]
        fp_path = Path(fp_path_str)

        if not fp_path.exists():
            logger.warning(f"Footprint file not found: {fp_path}")
            return

        # Register the footprint library so the build can find it
        fp_lib_name = fp_path.parent.name
        fp_dir = fp_path.parent
        lifecycle = PartLifecycle.singleton()
        lifecycle.library._insert_fp_lib(fp_lib_name, fp_dir)

        # Create the kicad library footprint trait with deferred loading
        kicad_fp_trait = fabll.Traits.create_and_add_instance_to(
            node=self, trait=F.KiCadFootprints.has_associated_kicad_library_footprint
        )
        try:
            kicad_fp_trait.setup(
                kicad_footprint_file_path=fp_path_str,
                library_name=fp_lib_name,
            )
        except ValueError as e:
            logger.warning(f"Could not parse footprint {fp_path}: {e}")

    @staticmethod
    def _validate_params(width: float, pin_count: int, pad_type: "NetTie.PadType"):
        """Validate the footprint parameters."""
        width_mm = f"{width:.1f}mm"
        supported_width = (
            ["0.5mm", "2.0mm"]
            if pad_type == NetTie.PadType.SMD
            else ["0.3mm", "1.0mm"]
        )
        if width_mm not in supported_width:
            raise UserBadParameterError(
                f"Width [{width_mm}] is currently not supported for NetTie with "
                f"pad type [{pad_type.name}]. "
                f"Supported widths are: {supported_width}."
            )

        if pin_count < 2 or pin_count > 4:
            raise UserBadParameterError(
                f"Pin count [{pin_count}] is currently not supported for NetTie. "
                f"Supported pin counts are: [2, 3, 4]"
            )

    @classmethod
    @once
    def factory(
        cls,
        width: float,
        pin_count: int,
        pad_type: PadType,
        connect_gnd: bool,
    ) -> type[Self]:
        """
        Create a concrete NetTie type with specific parameters.
        """
        # Validate parameters
        cls._validate_params(width, pin_count, pad_type)

        # Build footprint name
        width_mm = f"{width:.1f}mm"
        fp_name = f"NetTie-{pin_count}_{pad_type}_Pad{width_mm}"

        # Create concrete type name
        type_name = (
            f"NetTie<width={width}, pin_count={pin_count}, "
            f'pad_type="{pad_type.name}", connect_gnd={connect_gnd}>'
        )

        # Create concrete type
        ConcreteNetTie = fabll.Node._copy_type(cls, name=type_name)

        # Get footprint path
        fp_lib_name = "NetTie"
        fp_dir = Path(__file__).parent / "footprints" / fp_lib_name
        fp_path = fp_dir / f"{fp_name}.kicad_mod"

        # Add footprint path as literal constraint
        fp_path_constraint = F.Literals.Strings.MakeChild_ConstrainToLiteral(
            [cls._footprint_file_path], str(fp_path)
        )
        ConcreteNetTie._handle_cls_attr("_fp_path_constraint", fp_path_constraint)

        # Create power interfaces with indexed names and link to PointerSequence
        # The power PointerSequence is inherited from the base NetTie class
        for i in range(pin_count):
            pwr = F.ElectricPower.MakeChild()
            ConcreteNetTie._handle_cls_attr(f"power[{i}]", pwr)

            # Create MakeLink edge from inherited PointerSequence to element
            # This allows iteration: for p in nettie.power
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.power],
                elem_ref=[pwr],
                index=i,
            )
            ConcreteNetTie._handle_cls_attr(f"_power_link_{i}", edge)

            # Add requires_external_usage trait for all except first power
            if i > 0:
                pwr.add_dependant(
                    fabll.Traits.MakeEdge(
                        F.requires_external_usage.MakeChild(), [pwr]
                    )
                )

        # TODO: Add can_bridge trait for 2-pin netties
        # The bridge syntax with indexed paths like ["power[0]", "lv"] may not work
        # Need to investigate the correct path syntax for indexed children
        # For now, bridging may need to be done via explicit connections in .ato

        return ConcreteNetTie

    @classmethod
    def MakeChild(
        cls,
        width: float = 0.5,
        pin_count: int = 2,
        pad_type: str = "SMD",
        connect_gnd: bool = True,
    ) -> fabll._ChildField[Self]:
        """
        Create a NetTie child field with the specified parameters.

        Args:
            width: Pad width in mm (SMD: 0.5 or 2.0, THT: 0.3 or 1.0)
            pin_count: Number of pins (2, 3, or 4)
            pad_type: "SMD" or "THT"
            connect_gnd: If True, bridge connects lv (ground), else hv
        """
        # Convert pad_type string to enum
        if isinstance(pad_type, str):
            try:
                pad_type_enum = cls.PadType[pad_type]
            except KeyError:
                raise ValueError(
                    f"Unsupported pad type: {pad_type}. "
                    f"Supported types: {[p.name for p in cls.PadType]}"
                )
        else:
            pad_type_enum = pad_type

        # Use factory to create concrete type
        ConcreteNetTie = cls.factory(width, pin_count, pad_type_enum, connect_gnd)
        return cast(fabll._ChildField[Self], fabll._ChildField(ConcreteNetTie))
