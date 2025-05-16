import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.util import times
from faebryk.libs.library import L


class I2CIsolator(Module):
    """
    Connects two I2C interfaces together, without connecting the electricals below
    Useful for passing logical connections through isolators/switches etc.
    """

    @L.rt_field
    def power_rails(self) -> list[F.ElectricPower]:
        return times(2, F.ElectricPower)

    @L.rt_field
    def i2cs(self) -> list[F.I2C]:
        return times(2, F.I2C)

    def __preinit__(self) -> None:
        self.i2cs[0].connect_shallow(self.i2cs[1])
