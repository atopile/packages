# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, StrEnum
from pathlib import Path

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.iso_metric_screw_thread import Iso262_MetricScrewThreadSizes
from faebryk.libs.library import L
from faebryk.libs.part_lifecycle import PartLifecycle

logger = logging.getLogger(__name__)


class MountingHole(Module):
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

    contact: F.Electrical

    attach_to_footprint: F.can_attach_to_footprint_symmetrically
    designator_prefix = L.f_field(F.has_designator_prefix)(
        F.has_designator_prefix.Prefix.H
    )
    has_part_removed: F.has_part_removed

    def footprint_name(self) -> str:
        # e.g. MountingHole_2.7mm_M2.5_Pad_TopOnly
        size_metric = self._metric_screw_size
        size_mm = f"{size_metric.value}mm"
        padtype_name = self._pad_type.value
        if padtype_name:
            padtype_name = f"_{padtype_name}"

        return f"MountingHole_{size_mm}_{size_metric.name}{padtype_name}"

    def __init__(self, metric_screw_size: SupportedMetricScrewSizes, pad_type: PadType):
        super().__init__()
        self._metric_screw_size = metric_screw_size
        self._pad_type = pad_type

    def __preinit__(self):
        fp_name = self.footprint_name()
        fp_lib_name = "MountingHole"
        fp_dir = Path(__file__).parent / "footprints" / fp_lib_name
        fp_path = fp_dir / f"{fp_name}.kicad_mod"

        fp = F.KicadFootprint.from_path(fp_path, lib_name=fp_lib_name)
        self.get_trait(F.can_attach_to_footprint).attach(fp)

        lifecycle = PartLifecycle.singleton()
        lifecycle.library._insert_fp_lib(fp_lib_name, fp_dir)
