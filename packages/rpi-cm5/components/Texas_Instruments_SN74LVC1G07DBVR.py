# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401


logger = logging.getLogger(__name__)


class _Texas_Instruments_SN74LVC1G07DBVR(Module):
    """
    TODO: Docstring describing your module

    1 32mA 1.65V~5.5V 1 SOT-23-5 Buffers, Drivers, Receivers, Transceivers ROHS
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    # TODO: Change auto-generated interface types to actual high level types
    N_C_: F.Electrical  # pin: 1
    A: F.Electrical  # pin: 2
    GND: F.Electrical  # pin: 3
    Y: F.Electrical  # pin: 4
    VCC: F.Electrical  # pin: 5

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    explicit_part = L.f_field(F.has_explicit_part.by_supplier)("C7829")
    designator_prefix = L.f_field(F.has_designator_prefix)("U")

    @L.rt_field
    def attach_via_pinmap(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "1": self.N_C_,
                "2": self.A,
                "3": self.GND,
                "4": self.Y,
                "5": self.VCC,
            }
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        pass


class Texas_Instruments_SN74LVC1G07DBVR(Module):
    """
    Buffer
    """

    power: F.ElectricPower
    input: F.ElectricLogic
    output: F.ElectricLogic
    ic: _Texas_Instruments_SN74LVC1G07DBVR

    def __preinit__(self):
        self.power.hv.connect(self.ic.VCC)
        self.power.lv.connect(self.ic.GND)
        self.input.line.connect(self.ic.A)
        self.output.line.connect(self.ic.Y)
