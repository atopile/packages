import faebryk.library._F as F
from faebryk.libs.library import L


class ESDA25P35_1U1M(F.Diode):
    """
    TODO: Docstring describing your module

    35A@(8/20us) 41V 1.4kW 23.3V 22V DFN1610-2
    ESD and Surge Protection (TVS/ESD) ROHS
    """

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    explicit_part = L.f_field(F.has_explicit_part.by_supplier)("C1974707")
    designator_prefix = L.f_field(F.has_designator_prefix)("D")

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={self.anode: ["1"], self.cathode: ["2"]},
            accept_prefix=False,
            case_sensitive=False,
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        pass
