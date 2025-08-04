from enum import Enum, StrEnum
import faebryk.library._F as F  # noqa: F401
from faebryk.libs.units import P, dimensionless  # noqa: F401
from faebryk.core.module import Module  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.util import times  # noqa: F401
from faebryk.libs.smd import SMDSize


class SpiMode(StrEnum):
    """SPI mode configuration values"""

    MASTER = "MASTER"
    PERIPHERAL = "PERIPHERAL"


class PHAPOL(StrEnum):
    """PHAPOL configuration values"""

    CLK_LOW_FIRST_EDGE = "CLK_LOW_FIRST_EDGE"
    CLK_LOW_SECOND_EDGE = "CLK_LOW_SECOND_EDGE"
    CLK_HIGH_FIRST_EDGE = "CLK_HIGH_FIRST_EDGE"
    CLK_HIGH_SECOND_EDGE = "CLK_HIGH_SECOND_EDGE"


class XCVRMD(StrEnum):
    """XCVRMD configuration values"""

    BIDIRECTIONAL_STANDARD = "BIDIRECTIONAL_STANDARD"
    BIDIRECTIONAL_STANDARD_LPCM = "BIDIRECTIONAL_STANDARD_LPCM"
    UNIDIRECTIONAL_4MBPS = "UNIDIRECTIONAL_4MBPS"
    BIDIRECTIONAL_2MBPS = "BIDIRECTIONAL_2MBPS"


class RTO(Enum):
    """RTO configuration values in kOhms"""

    TIMEOUT_1_5_SEC = 0
    TIMEOUT_3_SEC = 17.8
    TIMEOUT_6_SEC = 30.9
    TIMEOUT_12_SEC = 43.2
    TIMEOUT_18_SEC = 56.2
    TIMEOUT_24_SEC = 68.1
    TIMEOUT_48_SEC = 80.6


class ADI_ADBMS6822_Configurator(Module):
    """
    The ADIBMS6822 Configurator contains the ADBMS6822 ato module and allows configuration of the ADBMS6822:

    :param spi_mode_selects: List of SPI Mode Selects
    :param phapols: List of phase/polarity of spi clock
    :param xcvrmds: List of transceiver mode
    :param rtos: List of LPCM timeout
    """

    def __init__(
        self,
        spi_mode_1: str,
        spi_mode_2: str,
        phapol_1: str,
        phapol_2: str,
        xcvrmd_1: str,
        xcvrmd_2: str,
        rto_1: str,
        rto_2: str,
    ):
        super().__init__()
        # Validate SPI mode inputs
        self.spi_mode_1 = SpiMode(spi_mode_1)
        self.spi_mode_2 = SpiMode(spi_mode_2)
        self.phapol_1 = PHAPOL(phapol_1)
        self.phapol_2 = PHAPOL(phapol_2)
        self.xcvrmd_1 = XCVRMD(xcvrmd_1)
        self.xcvrmd_2 = XCVRMD(xcvrmd_2)
        self.rto_1 = RTO[rto_1]
        self.rto_2 = RTO[rto_2]

    spi_mode_1_signal: F.ElectricSignal
    spi_mode_2_signal: F.ElectricSignal
    phapol_1_signal: F.ElectricSignal
    phapol_2_signal: F.ElectricSignal
    xcvrmd_1_signal: F.ElectricSignal
    xcvrmd_2_signal: F.ElectricSignal
    rto_1_signal: F.ElectricSignal
    rto_2_signal: F.ElectricSignal

    @L.rt_field
    def configuration_resistors(self) -> list[F.Resistor]:
        return times(8, F.Resistor)

    def __preinit__(self):
        for resistor in self.configuration_resistors:
            resistor.add(F.has_package_requirements(size=SMDSize.I0402))

        # --- SPI MODE 1 ---
        self.configuration_resistors[0].resistance.constrain_subset(
            L.Range.from_center_rel(10 * P.kohms, 5 * P.percent)
        )
        if self.spi_mode_1 == SpiMode.MASTER:
            self.spi_mode_1_signal.line.connect_via(
                self.configuration_resistors[0], self.spi_mode_1_signal.reference.hv
            )
        elif self.spi_mode_1 == SpiMode.PERIPHERAL:
            self.spi_mode_1_signal.line.connect_via(
                self.configuration_resistors[0], self.spi_mode_1_signal.reference.lv
            )
        else:
            raise ValueError(f"Invalid SPI mode: {self.spi_mode_1}")

        # --- SPI MODE 2 ---
        self.configuration_resistors[1].resistance.constrain_subset(
            L.Range.from_center_rel(10 * P.kohms, 5 * P.percent)
        )
        if self.spi_mode_2 == SpiMode.MASTER:
            self.spi_mode_2_signal.line.connect_via(
                self.configuration_resistors[1], self.spi_mode_2_signal.reference.hv
            )
        elif self.spi_mode_2 == SpiMode.PERIPHERAL:
            self.spi_mode_2_signal.line.connect_via(
                self.configuration_resistors[1], self.spi_mode_2_signal.reference.lv
            )
        else:
            raise ValueError(f"Invalid SPI mode: {self.spi_mode_2}")

        # --- PHAPOL 1 ---
        if self.phapol_1 == PHAPOL.CLK_LOW_FIRST_EDGE:
            self.configuration_resistors[2].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.phapol_1_signal.line.connect_via(
                self.configuration_resistors[2], self.phapol_1_signal.reference.lv
            )
        elif self.phapol_1 == PHAPOL.CLK_LOW_SECOND_EDGE:
            self.configuration_resistors[2].resistance.constrain_subset(
                L.Range.from_center_rel(20 * P.kohms, 5 * P.percent)
            )
            self.phapol_1_signal.line.connect_via(
                self.configuration_resistors[2], self.phapol_1_signal.reference.lv
            )
        elif self.phapol_1 == PHAPOL.CLK_HIGH_FIRST_EDGE:
            self.configuration_resistors[2].resistance.constrain_subset(
                L.Range.from_center_rel(100 * P.kohms, 5 * P.percent)
            )
            self.phapol_1_signal.line.connect_via(
                self.configuration_resistors[2], self.phapol_1_signal.reference.lv
            )
        elif self.phapol_1 == PHAPOL.CLK_HIGH_SECOND_EDGE:
            self.configuration_resistors[2].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.phapol_1_signal.line.connect_via(
                self.configuration_resistors[2], self.phapol_1_signal.reference.hv
            )
        else:
            raise ValueError(f"Invalid PHAPOL: {self.phapol_1}")

        # --- PHAPOL 2 ---
        if self.phapol_2 == PHAPOL.CLK_LOW_FIRST_EDGE:
            self.configuration_resistors[3].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.phapol_2_signal.line.connect_via(
                self.configuration_resistors[3], self.phapol_2_signal.reference.lv
            )
        elif self.phapol_2 == PHAPOL.CLK_LOW_SECOND_EDGE:
            self.configuration_resistors[3].resistance.constrain_subset(
                L.Range.from_center_rel(20 * P.kohms, 5 * P.percent)
            )
            self.phapol_2_signal.line.connect_via(
                self.configuration_resistors[3], self.phapol_2_signal.reference.lv
            )
        elif self.phapol_2 == PHAPOL.CLK_HIGH_FIRST_EDGE:
            self.configuration_resistors[3].resistance.constrain_subset(
                L.Range.from_center_rel(100 * P.kohms, 5 * P.percent)
            )
            self.phapol_2_signal.line.connect_via(
                self.configuration_resistors[3], self.phapol_2_signal.reference.lv
            )
        elif self.phapol_2 == PHAPOL.CLK_HIGH_SECOND_EDGE:
            self.configuration_resistors[3].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.phapol_2_signal.line.connect_via(
                self.configuration_resistors[3], self.phapol_2_signal.reference.hv
            )
        else:
            raise ValueError(f"Invalid PHAPOL: {self.phapol_2}")

        # --- XCVRMD 1 ---
        if self.xcvrmd_1 == XCVRMD.BIDIRECTIONAL_STANDARD:
            self.configuration_resistors[4].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.xcvrmd_1_signal.line.connect_via(
                self.configuration_resistors[4], self.xcvrmd_1_signal.reference.lv
            )
        elif self.xcvrmd_1 == XCVRMD.BIDIRECTIONAL_STANDARD_LPCM:
            self.configuration_resistors[4].resistance.constrain_subset(
                L.Range.from_center_rel(20 * P.kohms, 5 * P.percent)
            )
            self.xcvrmd_1_signal.line.connect_via(
                self.configuration_resistors[4], self.xcvrmd_1_signal.reference.lv
            )
        elif self.xcvrmd_1 == XCVRMD.UNIDIRECTIONAL_4MBPS:
            self.configuration_resistors[4].resistance.constrain_subset(
                L.Range.from_center_rel(100 * P.kohms, 5 * P.percent)
            )
            self.xcvrmd_1_signal.line.connect_via(
                self.configuration_resistors[4], self.xcvrmd_1_signal.reference.lv
            )
        elif self.xcvrmd_1 == XCVRMD.BIDIRECTIONAL_2MBPS:
            self.configuration_resistors[4].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.xcvrmd_1_signal.line.connect_via(
                self.configuration_resistors[4], self.xcvrmd_1_signal.reference.hv
            )
        else:
            raise ValueError(f"Invalid XCVRMD: {self.xcvrmd_1}")

        # --- XCVRMD 2 ---
        if self.xcvrmd_2 == XCVRMD.BIDIRECTIONAL_STANDARD:
            self.configuration_resistors[5].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.xcvrmd_2_signal.line.connect_via(
                self.configuration_resistors[5], self.xcvrmd_2_signal.reference.lv
            )
        elif self.xcvrmd_2 == XCVRMD.BIDIRECTIONAL_STANDARD_LPCM:
            self.configuration_resistors[5].resistance.constrain_subset(
                L.Range.from_center_rel(20 * P.kohms, 5 * P.percent)
            )
            self.xcvrmd_2_signal.line.connect_via(
                self.configuration_resistors[5], self.xcvrmd_2_signal.reference.lv
            )
        elif self.xcvrmd_2 == XCVRMD.UNIDIRECTIONAL_4MBPS:
            self.configuration_resistors[5].resistance.constrain_subset(
                L.Range.from_center_rel(100 * P.kohms, 5 * P.percent)
            )
            self.xcvrmd_2_signal.line.connect_via(
                self.configuration_resistors[5], self.xcvrmd_2_signal.reference.lv
            )
        elif self.xcvrmd_2 == XCVRMD.BIDIRECTIONAL_2MBPS:
            self.configuration_resistors[5].resistance.constrain_subset(
                L.Range.from_center_rel(10 * P.ohms, 5 * P.percent)
            )
            self.xcvrmd_2_signal.line.connect_via(
                self.configuration_resistors[5], self.xcvrmd_2_signal.reference.hv
            )
        else:
            raise ValueError(f"Invalid XCVRMD: {self.xcvrmd_2}")

        # --- RTO 1 ---
        self.configuration_resistors[6].resistance.constrain_subset(
            L.Range.from_center_rel(self.rto_1.value * P.kohms, 5 * P.percent)
        )
        self.rto_1_signal.line.connect_via(
            self.configuration_resistors[6], self.rto_1_signal.reference.lv
        )

        # --- RTO 2 ---
        self.configuration_resistors[7].resistance.constrain_subset(
            L.Range.from_center_rel(self.rto_2.value * P.kohms, 5 * P.percent)
        )
        self.rto_2_signal.line.connect_via(
            self.configuration_resistors[7], self.rto_2_signal.reference.lv
        )
