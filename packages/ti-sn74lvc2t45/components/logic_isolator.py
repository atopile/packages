import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class LogicIsolator(Module):
    """
    Connects two I2C interfaces together, without connecting the electricals below
    Useful for passing logical connections through isolators/switches etc.
    """

    a: F.ElectricLogic
    b: F.ElectricLogic

    def __preinit__(self) -> None:
        self.a.connect_shallow(self.b)

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.a, self.b)
