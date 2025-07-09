import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class ESDA25W(Module):
    """
    25V 400W 25V 24V SOT-323-3L
    ESD and Surge Protection (TVS/ESD) ROHS
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    # TODO: Change auto-generated interface types to actual high level types
    A: F.Electrical
    K1: F.Electrical
    K2: F.Electrical
    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    explicit_part = L.f_field(F.has_explicit_part.by_supplier)("C2935152")
    designator_prefix = L.f_field(F.has_designator_prefix)("D")

    @L.rt_field
    def pin_association(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "3": self.A,
                "1": self.K1,
                "2": self.K2,
            }
        )
