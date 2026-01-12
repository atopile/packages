# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, StrEnum
from pathlib import Path
from typing import Self, cast

import faebryk.core.node as fabll
import faebryk.library._F as F
from faebryk.libs.iso_metric_screw_thread import Iso262_MetricScrewThreadSizes
from faebryk.libs.util import once

logger = logging.getLogger(__name__)


class MountingHole(fabll.Node):
    """
    Mounting hole component for PCB mechanical attachment.

    Supports various metric screw sizes (M2 to M8) and pad configurations.
    Use with MODULE_TEMPLATING in ato files.

    Example usage in ato:
        m3_with_pad = new MountingHole<metric_screw_size="M3", pad_type="Pad">
        m6_no_pad = new MountingHole<metric_screw_size="M6", pad_type="NoPad">
    """

    class PadType(StrEnum):
        NoPad = ""
        Pad = "Pad"
        Pad_TopBottom = "Pad_TopBottom"
        Pad_TopOnly = "Pad_TopOnly"
        Pad_Via = "Pad_Via"

    # We currently only have footprints for these sizes
    class SupportedMetricScrewSizes(Enum):
        M2 = Iso262_MetricScrewThreadSizes.M2.value
        M2_5 = Iso262_MetricScrewThreadSizes.M2_5.value
        M3 = Iso262_MetricScrewThreadSizes.M3.value
        M4 = Iso262_MetricScrewThreadSizes.M4.value
        M5 = Iso262_MetricScrewThreadSizes.M5.value
        M6 = Iso262_MetricScrewThreadSizes.M6.value
        M8 = Iso262_MetricScrewThreadSizes.M8.value

    # Mark as abstract - concrete types are created via factory
    is_abstract = fabll.Traits.MakeEdge(fabll.is_abstract.MakeChild()).put_on_type()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())

    # Part is removed - mounting holes don't go through part picking
    _has_part_removed = fabll.Traits.MakeEdge(F.has_part_removed.MakeChild())

    # Can attach to footprint
    _can_attach_to_footprint = fabll.Traits.MakeEdge(
        F.Footprints.can_attach_to_footprint.MakeChild()
    )

    # Designator prefix H for hardware/holes
    _designator_prefix = fabll.Traits.MakeEdge(
        F.has_designator_prefix.MakeChild(F.has_designator_prefix.Prefix.H)
    )

    # Footprint file path - set by factory
    _footprint_file_path = F.Parameters.StringParameter.MakeChild()

    # Design check for footprint registration
    design_check = fabll.Traits.MakeEdge(F.implements_design_check.MakeChild())

    usage_example = fabll.Traits.MakeEdge(
        F.has_usage_example.MakeChild(
            example="""
        from "MountingHole.py" import MountingHole

        # M3 mounting hole with top and bottom pads
        m3_padded = new MountingHole<metric_screw_size="M3", pad_type="Pad">

        # M6 mounting hole without pads
        m6_no_pad = new MountingHole<metric_screw_size="M6", pad_type="NoPad">

        # M3 with top-only pad for grounding
        m3_top = new MountingHole<metric_screw_size="M3", pad_type="Pad_TopOnly">

        # Connect padded holes for grounding
        m3_padded.contact ~ m3_top.contact
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
            logger.warning("Footprint path not set for MountingHole")
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
        # Setup will attempt to load the footprint - may fail due to format issues
        try:
            kicad_fp_trait.setup(
                kicad_footprint_file_path=fp_path_str,
                library_name=fp_lib_name,
            )
        except ValueError as e:
            logger.warning(f"Could not parse footprint {fp_path}: {e}")
            # Even if parsing fails, the footprint library is registered
            # and the build process may still be able to use it

    @classmethod
    @once
    def factory(
        cls, metric_screw_size: SupportedMetricScrewSizes, pad_type: PadType
    ) -> type[Self]:
        """
        Create a concrete MountingHole type with specific screw size and pad type.
        """
        # Build footprint name
        size_mm = f"{metric_screw_size.value}mm"
        padtype_name = pad_type.value
        if padtype_name:
            padtype_name = f"_{padtype_name}"
        fp_name = f"MountingHole_{size_mm}_{metric_screw_size.name}{padtype_name}"

        # Create concrete type
        ConcreteMountingHole = fabll.Node._copy_type(
            cls,
            name=f'MountingHole<metric_screw_size="{metric_screw_size.name}", '
            f'pad_type="{pad_type.name}">',
        )

        # Get footprint path
        fp_lib_name = "MountingHole"
        fp_dir = Path(__file__).parent / "footprints" / fp_lib_name
        fp_path = fp_dir / f"{fp_name}.kicad_mod"

        # Add footprint path as literal constraint
        fp_path_constraint = F.Literals.Strings.MakeChild_ConstrainToLiteral(
            [cls._footprint_file_path], str(fp_path)
        )
        ConcreteMountingHole._handle_cls_attr("_fp_path_constraint", fp_path_constraint)

        # Add contact electrical interface if pad type has a pad
        if pad_type != cls.PadType.NoPad:
            contact = F.Electrical.MakeChild()
            ConcreteMountingHole._handle_cls_attr("contact", contact)

            # Add lead trait to contact for pinmap
            contact.add_dependant(
                fabll.Traits.MakeEdge(F.Lead.is_lead.MakeChild(), [contact])
            )

        return ConcreteMountingHole

    @classmethod
    def MakeChild(
        cls, metric_screw_size: str = "M3", pad_type: str = "Pad"
    ) -> fabll._ChildField[Self]:
        """
        Create a MountingHole child field with the specified screw size and pad type.

        Args:
            metric_screw_size: One of M2, M2_5, M3, M4, M5, M6, M8
            pad_type: One of NoPad, Pad, Pad_TopBottom, Pad_TopOnly, Pad_Via
        """
        # Convert string parameters to enum values
        try:
            screw_size_enum = cls.SupportedMetricScrewSizes[metric_screw_size]
        except KeyError:
            raise ValueError(
                f"Unsupported metric screw size: {metric_screw_size}. "
                f"Supported sizes: {[s.name for s in cls.SupportedMetricScrewSizes]}"
            )

        try:
            pad_type_enum = cls.PadType[pad_type]
        except KeyError:
            raise ValueError(
                f"Unsupported pad type: {pad_type}. "
                f"Supported types: {[p.name for p in cls.PadType]}"
            )

        # Use factory to create concrete type
        ConcreteMountingHole = cls.factory(screw_size_enum, pad_type_enum)
        return cast(fabll._ChildField[Self], fabll._ChildField(ConcreteMountingHole))
