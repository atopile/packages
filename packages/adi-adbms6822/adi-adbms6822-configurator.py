# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
ADBMS6822 Configuration Module

This module implements the configuration resistor network for the ADI ADBMS6822
isoSPI transceiver IC. The ADBMS6822 uses resistor-set configuration pins to
configure various operating modes:

- SPI Mode (MSTR): Master or Peripheral mode
- PHAPOL: SPI clock phase and polarity
- XCVRMD: Transceiver operating mode
- RTO: Low Power Communication Mode timeout period

Each configuration is set via a resistor connected between the config pin
and either VCC (hv) or GND (lv), with specific resistance values for
multi-level inputs.
"""

import logging
from enum import Enum, StrEnum
from typing import Self, cast

import faebryk.core.faebrykpy as fbrk
import faebryk.core.node as fabll
import faebryk.library._F as F
from faebryk.core import graph
from faebryk.libs.smd import SMDSize
from faebryk.libs.util import once

logger = logging.getLogger(__name__)


class SpiMode(StrEnum):
    """SPI mode configuration values"""

    MASTER = "MASTER"
    PERIPHERAL = "PERIPHERAL"


class PHAPOL(StrEnum):
    """PHAPOL configuration values for SPI clock phase and polarity"""

    CLK_LOW_FIRST_EDGE = "CLK_LOW_FIRST_EDGE"
    CLK_LOW_SECOND_EDGE = "CLK_LOW_SECOND_EDGE"
    CLK_HIGH_FIRST_EDGE = "CLK_HIGH_FIRST_EDGE"
    CLK_HIGH_SECOND_EDGE = "CLK_HIGH_SECOND_EDGE"


class XCVRMD(StrEnum):
    """XCVRMD configuration values for transceiver operating mode"""

    BIDIRECTIONAL_STANDARD = "BIDIRECTIONAL_STANDARD"
    BIDIRECTIONAL_STANDARD_LPCM = "BIDIRECTIONAL_STANDARD_LPCM"
    UNIDIRECTIONAL_4MBPS = "UNIDIRECTIONAL_4MBPS"
    BIDIRECTIONAL_2MBPS = "BIDIRECTIONAL_2MBPS"


class RTO(Enum):
    """RTO configuration values - resistance in kOhms for timeout period"""

    TIMEOUT_1_5_SEC = 0  # Direct to GND (0 ohm or short)
    TIMEOUT_3_SEC = 17.8
    TIMEOUT_6_SEC = 30.9
    TIMEOUT_12_SEC = 43.2
    TIMEOUT_18_SEC = 56.2
    TIMEOUT_24_SEC = 68.1
    TIMEOUT_48_SEC = 80.6


# Resistance lookup tables (in ohms)
PHAPOL_RESISTANCE = {
    PHAPOL.CLK_LOW_FIRST_EDGE: 10.0,  # 10 ohm to GND
    PHAPOL.CLK_LOW_SECOND_EDGE: 20000.0,  # 20k to GND
    PHAPOL.CLK_HIGH_FIRST_EDGE: 100000.0,  # 100k to GND
    PHAPOL.CLK_HIGH_SECOND_EDGE: 10.0,  # 10 ohm to VCC
}

PHAPOL_TO_HV = {
    PHAPOL.CLK_LOW_FIRST_EDGE: False,
    PHAPOL.CLK_LOW_SECOND_EDGE: False,
    PHAPOL.CLK_HIGH_FIRST_EDGE: False,
    PHAPOL.CLK_HIGH_SECOND_EDGE: True,
}

XCVRMD_RESISTANCE = {
    XCVRMD.BIDIRECTIONAL_STANDARD: 10.0,  # 10 ohm to GND
    XCVRMD.BIDIRECTIONAL_STANDARD_LPCM: 20000.0,  # 20k to GND
    XCVRMD.UNIDIRECTIONAL_4MBPS: 100000.0,  # 100k to GND
    XCVRMD.BIDIRECTIONAL_2MBPS: 10.0,  # 10 ohm to VCC
}

XCVRMD_TO_HV = {
    XCVRMD.BIDIRECTIONAL_STANDARD: False,
    XCVRMD.BIDIRECTIONAL_STANDARD_LPCM: False,
    XCVRMD.UNIDIRECTIONAL_4MBPS: False,
    XCVRMD.BIDIRECTIONAL_2MBPS: True,
}


class ADI_ADBMS6822_Configurator(fabll.Node):
    """
    Configuration resistor network for ADBMS6822 isoSPI transceiver.

    This module creates 8 configuration resistors that connect between
    configuration signal lines and power rails (VCC or GND) to set the
    device operating modes.

    Configuration parameters (from ato template):
        spi_mode_1, spi_mode_2: "MASTER" or "PERIPHERAL"
        phapol_1, phapol_2: Clock phase/polarity setting
        xcvrmd_1, xcvrmd_2: Transceiver mode
        rto_1, rto_2: LPCM timeout period
    """

    # ----------------------------------------
    #     interfaces (signals to configure)
    # ----------------------------------------
    spi_mode_1_signal = F.ElectricSignal.MakeChild()
    spi_mode_2_signal = F.ElectricSignal.MakeChild()
    phapol_1_signal = F.ElectricSignal.MakeChild()
    phapol_2_signal = F.ElectricSignal.MakeChild()
    xcvrmd_1_signal = F.ElectricSignal.MakeChild()
    xcvrmd_2_signal = F.ElectricSignal.MakeChild()
    rto_1_signal = F.ElectricSignal.MakeChild()
    rto_2_signal = F.ElectricSignal.MakeChild()

    # ----------------------------------------
    #     resistors (created dynamically)
    # ----------------------------------------
    # PointerSequence for iteration - elements added by factory
    configuration_resistors = F.Collections.PointerSequence.MakeChild()

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    _single_electric_reference = fabll.Traits.MakeEdge(
        F.has_single_electric_reference.MakeChild()
    )

    # Mark as abstract since factory creates concrete implementations
    is_abstract = fabll.Traits.MakeEdge(fabll.is_abstract.MakeChild()).put_on_type()

    @classmethod
    @once
    def factory(
        cls,
        spi_mode_1: str,
        spi_mode_2: str,
        phapol_1: str,
        phapol_2: str,
        xcvrmd_1: str,
        xcvrmd_2: str,
        rto_1: str,
        rto_2: str,
    ) -> type[Self]:
        """
        Create a concrete ADI_ADBMS6822_Configurator type with specific configuration.

        This factory:
        1. Creates 8 resistors with appropriate values
        2. Connects each resistor between signal line and VCC or GND
        3. Sets package to 0402 for all resistors
        """
        # Parse enum values
        spi_mode_1_val = SpiMode(spi_mode_1)
        spi_mode_2_val = SpiMode(spi_mode_2)
        phapol_1_val = PHAPOL(phapol_1)
        phapol_2_val = PHAPOL(phapol_2)
        xcvrmd_1_val = XCVRMD(xcvrmd_1)
        xcvrmd_2_val = XCVRMD(xcvrmd_2)
        rto_1_val = RTO[rto_1]
        rto_2_val = RTO[rto_2]

        type_name = (
            f"ADI_ADBMS6822_Configurator<"
            f"spi_mode_1={spi_mode_1},spi_mode_2={spi_mode_2},"
            f"phapol_1={phapol_1},phapol_2={phapol_2},"
            f"xcvrmd_1={xcvrmd_1},xcvrmd_2={xcvrmd_2},"
            f"rto_1={rto_1},rto_2={rto_2}>"
        )

        ConcreteConfigurator = fabll.Node._copy_type(cls, name=type_name)

        # Create 8 resistors
        for i in range(8):
            resistor = F.Resistor.MakeChild()
            ConcreteConfigurator._handle_cls_attr(
                f"configuration_resistors[{i}]", resistor
            )
            edge = F.Collections.PointerSequence.MakeEdge(
                seq_ref=[cls.configuration_resistors],
                elem_ref=[resistor],
                index=i,
            )
            ConcreteConfigurator._handle_cls_attr(f"_resistor_link_{i}", edge)

            # Add package constraint (0402)
            pkg_constraint = fabll.Traits.MakeEdge(
                F.has_package_requirements.MakeChild(size=SMDSize.I0402),
                owner=[resistor],
            )
            ConcreteConfigurator._handle_cls_attr(f"_resistor_pkg_{i}", pkg_constraint)

        # Define configuration: (signal, resistor_idx, resistance_ohms, to_hv)
        configs = [
            # SPI Mode 1: 10k pullup (MASTER) or pulldown (PERIPHERAL)
            (
                cls.spi_mode_1_signal,
                0,
                10000.0,
                spi_mode_1_val == SpiMode.MASTER,
            ),
            # SPI Mode 2: 10k pullup (MASTER) or pulldown (PERIPHERAL)
            (
                cls.spi_mode_2_signal,
                1,
                10000.0,
                spi_mode_2_val == SpiMode.MASTER,
            ),
            # PHAPOL 1: Variable resistance, direction based on setting
            (
                cls.phapol_1_signal,
                2,
                PHAPOL_RESISTANCE[phapol_1_val],
                PHAPOL_TO_HV[phapol_1_val],
            ),
            # PHAPOL 2: Variable resistance, direction based on setting
            (
                cls.phapol_2_signal,
                3,
                PHAPOL_RESISTANCE[phapol_2_val],
                PHAPOL_TO_HV[phapol_2_val],
            ),
            # XCVRMD 1: Variable resistance, direction based on setting
            (
                cls.xcvrmd_1_signal,
                4,
                XCVRMD_RESISTANCE[xcvrmd_1_val],
                XCVRMD_TO_HV[xcvrmd_1_val],
            ),
            # XCVRMD 2: Variable resistance, direction based on setting
            (
                cls.xcvrmd_2_signal,
                5,
                XCVRMD_RESISTANCE[xcvrmd_2_val],
                XCVRMD_TO_HV[xcvrmd_2_val],
            ),
            # RTO 1: Resistor to GND (value in kohms from enum)
            (
                cls.rto_1_signal,
                6,
                rto_1_val.value * 1000.0 if rto_1_val.value > 0 else 10.0,
                False,
            ),
            # RTO 2: Resistor to GND (value in kohms from enum)
            (
                cls.rto_2_signal,
                7,
                rto_2_val.value * 1000.0 if rto_2_val.value > 0 else 10.0,
                False,
            ),
        ]

        for signal_field, resistor_idx, resistance_ohms, to_hv in configs:
            resistor_ref = f"configuration_resistors[{resistor_idx}]"

            # Constrain resistance value (5% tolerance)
            tolerance = 0.05
            res_constraint = F.Literals.Numbers.MakeChild_ConstrainToSubsetLiteral(
                param_ref=[resistor_ref, "resistance"],
                min=resistance_ohms * (1 - tolerance),
                max=resistance_ohms * (1 + tolerance),
                unit=F.Units.Ohm,
            )
            ConcreteConfigurator._handle_cls_attr(
                f"_res_constraint_{resistor_idx}", res_constraint
            )

            # Connect signal.line -> resistor.unnamed[0]
            signal_to_resistor = fabll.MakeEdge(
                [signal_field, "line"],
                [resistor_ref, "unnamed[0]"],  # type: ignore[list-item]
                edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
            )
            ConcreteConfigurator._handle_cls_attr(
                f"_signal_to_res_{resistor_idx}", signal_to_resistor
            )

            # Connect resistor.unnamed[1] -> signal.reference.hv or .lv
            if to_hv:
                resistor_to_rail = fabll.MakeEdge(
                    [resistor_ref, "unnamed[1]"],  # type: ignore[list-item]
                    [signal_field, "reference", "hv"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
            else:
                resistor_to_rail = fabll.MakeEdge(
                    [resistor_ref, "unnamed[1]"],  # type: ignore[list-item]
                    [signal_field, "reference", "lv"],
                    edge=fbrk.EdgeInterfaceConnection.build(shallow=False),
                )
            ConcreteConfigurator._handle_cls_attr(
                f"_res_to_rail_{resistor_idx}", resistor_to_rail
            )

        return ConcreteConfigurator

    @classmethod
    def MakeChild(  # type: ignore[override]
        cls,
        spi_mode_1: str = "MASTER",
        spi_mode_2: str = "MASTER",
        phapol_1: str = "CLK_HIGH_SECOND_EDGE",
        phapol_2: str = "CLK_HIGH_SECOND_EDGE",
        xcvrmd_1: str = "BIDIRECTIONAL_STANDARD",
        xcvrmd_2: str = "BIDIRECTIONAL_STANDARD",
        rto_1: str = "TIMEOUT_1_5_SEC",
        rto_2: str = "TIMEOUT_1_5_SEC",
    ) -> fabll._ChildField[Self]:
        """
        Create an ADI_ADBMS6822_Configurator child field with the specified configuration.

        Args:
            spi_mode_1, spi_mode_2: "MASTER" or "PERIPHERAL"
            phapol_1, phapol_2: Clock phase/polarity
                - "CLK_LOW_FIRST_EDGE"
                - "CLK_LOW_SECOND_EDGE"
                - "CLK_HIGH_FIRST_EDGE"
                - "CLK_HIGH_SECOND_EDGE"
            xcvrmd_1, xcvrmd_2: Transceiver mode
                - "BIDIRECTIONAL_STANDARD"
                - "BIDIRECTIONAL_STANDARD_LPCM"
                - "UNIDIRECTIONAL_4MBPS"
                - "BIDIRECTIONAL_2MBPS"
            rto_1, rto_2: LPCM timeout
                - "TIMEOUT_1_5_SEC", "TIMEOUT_3_SEC", "TIMEOUT_6_SEC"
                - "TIMEOUT_12_SEC", "TIMEOUT_18_SEC", "TIMEOUT_24_SEC"
                - "TIMEOUT_48_SEC"
        """
        logger.debug(
            f"ADI_ADBMS6822_Configurator.MakeChild called: "
            f"spi_mode_1={spi_mode_1}, spi_mode_2={spi_mode_2}"
        )

        ConcreteConfigurator = cls.factory(
            spi_mode_1=spi_mode_1,
            spi_mode_2=spi_mode_2,
            phapol_1=phapol_1,
            phapol_2=phapol_2,
            xcvrmd_1=xcvrmd_1,
            xcvrmd_2=xcvrmd_2,
            rto_1=rto_1,
            rto_2=rto_2,
        )

        return cast(fabll._ChildField[Self], fabll._ChildField(ConcreteConfigurator))

    usage_example = fabll.Traits.MakeEdge(
        F.has_usage_example.MakeChild(
            example="""
        import ADI_ADBMS6822_Configurator, ElectricSignal, ElectricPower

        # Create configurator with specific settings
        configurator = new ADI_ADBMS6822_Configurator<
            spi_mode_1="MASTER",
            spi_mode_2="MASTER",
            phapol_1="CLK_HIGH_SECOND_EDGE",
            phapol_2="CLK_HIGH_SECOND_EDGE",
            xcvrmd_1="BIDIRECTIONAL_STANDARD",
            xcvrmd_2="BIDIRECTIONAL_STANDARD",
            rto_1="TIMEOUT_1_5_SEC",
            rto_2="TIMEOUT_1_5_SEC"
        >

        # Connect configuration signals
        mstr_signal = new ElectricSignal
        power = new ElectricPower
        mstr_signal.reference ~ power
        configurator.spi_mode_1_signal ~ mstr_signal
        """,
            language=F.has_usage_example.Language.ato,
        ).put_on_type()
    )


# -----------------------------------------------------------------------------
#                                 Tests
# -----------------------------------------------------------------------------


def test_configurator_basic():
    """Test basic ADI_ADBMS6822_Configurator creation."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        configurator = ADI_ADBMS6822_Configurator.MakeChild()

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    assert app.configurator.get() is not None
    assert app.configurator.get().spi_mode_1_signal.get() is not None
    assert app.configurator.get().spi_mode_2_signal.get() is not None

    # Check resistors were created
    resistors = app.configurator.get().configuration_resistors.get().as_list()
    assert len(resistors) == 8


def test_configurator_master_mode():
    """Test configurator with MASTER SPI mode."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        configurator = ADI_ADBMS6822_Configurator.MakeChild(
            spi_mode_1="MASTER",
            spi_mode_2="PERIPHERAL",
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    resistors = app.configurator.get().configuration_resistors.get().as_list()
    assert len(resistors) == 8


def test_configurator_phapol_modes():
    """Test configurator with different PHAPOL settings."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        configurator = ADI_ADBMS6822_Configurator.MakeChild(
            phapol_1="CLK_LOW_FIRST_EDGE",
            phapol_2="CLK_HIGH_SECOND_EDGE",
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    resistors = app.configurator.get().configuration_resistors.get().as_list()
    assert len(resistors) == 8


def test_configurator_xcvrmd_modes():
    """Test configurator with different XCVRMD settings."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        configurator = ADI_ADBMS6822_Configurator.MakeChild(
            xcvrmd_1="UNIDIRECTIONAL_4MBPS",
            xcvrmd_2="BIDIRECTIONAL_2MBPS",
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    resistors = app.configurator.get().configuration_resistors.get().as_list()
    assert len(resistors) == 8


def test_configurator_rto_modes():
    """Test configurator with different RTO timeout settings."""
    g = graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)

    class _App(fabll.Node):
        _is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
        configurator = ADI_ADBMS6822_Configurator.MakeChild(
            rto_1="TIMEOUT_12_SEC",
            rto_2="TIMEOUT_48_SEC",
        )

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)

    resistors = app.configurator.get().configuration_resistors.get().as_list()
    assert len(resistors) == 8
