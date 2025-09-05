# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import StrEnum
from pathlib import Path

import faebryk.library._F as F
from atopile.errors import UserBadParameterError
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.part_lifecycle import PartLifecycle
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class NetTie(Module):
    """A net tie component that can bridge different interfaces."""

    class PadType(StrEnum):
        SMD = "SMD"
        THT = "THT"

    attach_to_footprint: F.can_attach_to_footprint_symmetrically
    designator_prefix = L.f_field(F.has_designator_prefix)(
        F.has_designator_prefix.Prefix.JP
    )
    picked: F.has_part_removed

    def footprint_name(self):
        # e.g. NetTie-2_SMD_Pad0.5mm
        width_mm = f"{self._width:.1f}mm"
        supported_width = (
            ["0.5mm", "2.0mm"]
            if self._pad_type == self.PadType.SMD
            else ["0.3mm", "1.0mm"]
        )
        if width_mm not in supported_width:
            raise UserBadParameterError(
                f"Width [{width_mm}] is currently not supported for NetTie with "
                f"pad type [{self._pad_type.name}]. "
                f"Supported widths are: {supported_width}."
            )

        if self._pin_count < 2 or self._pin_count > 4:
            raise UserBadParameterError(
                f"Pin count [{self._pin_count}] is currently not supported for NetTie. "
                f"Supported pin counts are: [2, 3, 4]"
            )

        return f"NetTie-{self._pin_count}_{self._pad_type}_Pad{width_mm}"

    @L.rt_field
    def power(self):
        return times(self._pin_count, F.ElectricPower)

    def __init__(
        self,
        width: float = 0.5,
        pin_count: int = 2,
        pad_type: PadType = PadType.SMD,
        connect_gnd: bool = True,
    ) -> None:
        super().__init__()
        self._width = width
        self._pin_count = pin_count
        if isinstance(pad_type, str):
            pad_type = self.PadType[pad_type]
        self._pad_type = pad_type
        self._connect_gnd = connect_gnd

    def __preinit__(self):
        if self._pin_count == 2:
            self.add(F.can_bridge_defined(*self.power))

        # Connect all interfaces to the first one
        for p in self.power[1:]:
            p.connect_shallow(self.power[0])
            p.add(F.requires_external_usage())

        # add footprint
        fp_name = self.footprint_name()
        fp_lib_name = "NetTie"
        fp_dir = Path(__file__).parent / "footprints" / fp_lib_name
        fp_path = fp_dir / f"{fp_name}.kicad_mod"

        fp = F.KicadFootprint.from_path(fp_path, lib_name=fp_lib_name)
        self.get_trait(F.can_attach_to_footprint).attach(fp)

        lifecycle = PartLifecycle.singleton()
        lifecycle.library._insert_fp_lib(fp_lib_name, fp_dir)

        # connect to footprint
        fp.get_trait(F.can_attach_via_pinmap).attach(
            pinmap={
                f"{i + 1}": power.lv if self._connect_gnd else power.hv
                for i, power in enumerate(self.power)
            }
        )
