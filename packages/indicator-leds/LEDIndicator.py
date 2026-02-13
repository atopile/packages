import faebryk.core.node as fabll
import faebryk.library._F as F

from typing import Self
from faebryk.libs.util import once
import pytest


class LEDIndicator(fabll.Node):
    """
    Simple indicator LED with a series resistor.
    Can be connected using either one of:
    - ElectricLogic
    - ElectricSignal
    - ElectricPower
    """

    is_module = fabll.Traits.MakeEdge(fabll.is_module.MakeChild())
    is_abstract = fabll.Traits.MakeEdge(fabll.is_abstract.MakeChild()).put_on_type()

    led = F.LED.MakeChild()
    resistor = F.Resistor.MakeChild()

    power = F.ElectricPower.MakeChild()
    logic = F.ElectricLogic.MakeChild()
    analog_signal = F.ElectricSignal.MakeChild()

    current = F.Parameters.NumericParameter.MakeChild(unit=F.Units.Ampere)
    _default_current = fabll.Traits.MakeEdge(
        F.has_default_constraint.MakeChild(
            literal=F.Literals.Numbers.MakeChild_FromCenterRel(
                center=0.00065,
                rel=0.00015,
                unit=F.Units.Ampere,
            )
        ),
        [current],
    )

    active_low = F.Parameters.BooleanParameter.MakeChild()

    _equations = [
        F.Expressions.Is.MakeChild(
            [resistor, F.Resistor.resistance],
            [
                _res := F.Expressions.Divide.MakeChild(
                    [
                        _v_res := F.Expressions.Subtract.MakeChild(
                            [power, F.ElectricPower.voltage],
                            [led, F.LED.diode, F.Diode.forward_voltage],
                        )
                    ],
                    [current],
                ),
            ],
            assert_=True,
        ),
        F.Expressions.LessOrEqual.MakeChild(
            [current],
            [led, F.LED.diode, F.Diode.max_current],
            assert_=True,
        ),
        F.Expressions.GreaterOrEqual.MakeChild(
            [power, F.ElectricPower.voltage],
            [led, F.LED.diode, F.Diode.forward_voltage],
            assert_=True,
        ),
    ]

    _connections = [
        # power.hv ~> led ~> resistor ~> power.lv
        # fabll.is_interface.MakeConnectionEdge(
        #     [power, F.ElectricPower.hv],
        #     [led, F.LED.diode, F.Diode.anode],
        # ),
        fabll.is_interface.MakeConnectionEdge(
            [led, F.LED.diode, F.Diode.cathode],
            [resistor, F.Resistor.unnamed[0]],
        ),
        # fabll.is_interface.MakeConnectionEdge(
        #     [resistor, F.Resistor.unnamed[1]],
        #     [power, F.ElectricPower.lv],
        # ),
        # logic.line ~ analog_signal.line
        fabll.is_interface.MakeConnectionEdge(
            [logic, F.ElectricLogic.line],
            [analog_signal, F.ElectricSignal.line],
        ),
        # power ~ logic/analog_signal.reference
        fabll.is_interface.MakeConnectionEdge(
            [power],
            [logic, F.ElectricLogic.reference],
            [analog_signal, F.ElectricSignal.reference],
        ),
    ]

    # _aliases = [
    #     F.Expressions.Is.MakeChild(
    #         [power, F.ElectricPower.voltage],
    #         [logic, F.ElectricLogic.reference, F.ElectricPower.voltage],
    #         [analog_signal, F.ElectricSignal.reference, F.ElectricPower.voltage],
    #         assert_=True,
    #     ),
    # ]

    @classmethod
    def MakeChild(cls, active_low: bool = False) -> fabll._ChildField[Self]:
        """
        Create a new LEDIndicator child field with the correct on/off state
        (active_low = True means the LED is on when the signal/logic line is low).

        Uses factory() to create a concrete type with the correct connections.
        """
        ConcreteLEDIndicator = cls.factory(active_low)
        out = fabll._ChildField(ConcreteLEDIndicator)
        return out

    @classmethod
    @once
    def factory(cls, active_low: bool) -> type[Self]:
        """
        Create a concrete LEDIndicator type with the correct connections.
        """
        ConcreteLEDIndicator = fabll.Node._copy_type(
            cls, name=f"LEDIndicator<active_low={active_low}>"
        )

        # TODO: set active_low parameter

        if active_low:
            # active low
            # logic/analog_signal.reference.hv ~> led ~> resistor ~> logic/analog_signal.line
            factory_connections = [
                fabll.is_interface.MakeConnectionEdge(
                    [
                        ConcreteLEDIndicator.logic,
                        F.ElectricLogic.reference,
                        F.ElectricPower.hv,
                    ],
                    [ConcreteLEDIndicator.led, F.LED.diode, F.Diode.anode],
                ),
                fabll.is_interface.MakeConnectionEdge(
                    [ConcreteLEDIndicator.resistor, F.Resistor.unnamed[1]],
                    [
                        ConcreteLEDIndicator.logic,
                        F.ElectricLogic.line,
                    ],
                ),
            ]
        else:
            # active high
            # logic/analog_signal.line ~> led ~> resistor ~> logic/analog_signal.reference.lv
            factory_connections = [
                fabll.is_interface.MakeConnectionEdge(
                    [
                        ConcreteLEDIndicator.logic,
                        F.ElectricLogic.line,
                    ],
                    [ConcreteLEDIndicator.led, F.LED.diode, F.Diode.anode],
                ),
                fabll.is_interface.MakeConnectionEdge(
                    [ConcreteLEDIndicator.resistor, F.Resistor.unnamed[1]],
                    [
                        ConcreteLEDIndicator.logic,
                        F.ElectricLogic.reference,
                        F.ElectricPower.lv,
                    ],
                ),
            ]

        # Add edge as a class field so it gets processed
        ConcreteLEDIndicator._handle_cls_attr(
            "_factory_connections", factory_connections
        )

        return ConcreteLEDIndicator


class TestLEDIndicator:
    @pytest.mark.parametrize("active_low", [True, False])
    def test_led_indicator_active_low_x(self, active_low: bool):
        """Test LEDIndicator with active_low=x."""
        from faebryk.core import graph
        import faebryk.core.faebrykpy as fbrk

        g = graph.GraphView.create()
        tg = fbrk.TypeGraph.create(g=g)

        class _App(fabll.Node):
            led_indicator: fabll._ChildField[LEDIndicator]
            pass

        # Dynamically add the addressor with the correct bit count
        _App._handle_cls_attr(
            "led_indicator", LEDIndicator.MakeChild(active_low=active_low)
        )

        app = _App.bind_typegraph(tg=tg).create_instance(g=g)
        led_indicator = app.led_indicator.get()

        # Check if the logic line is connected to the led.diode.anode if active_low is False
        # or the resistor.unnamed[1] to the logic.line if active_low is True
        if active_low:
            assert (
                led_indicator.led.get()
                .diode.get()
                .anode.get()
                ._is_interface.get()
                .is_connected_to(
                    led_indicator.logic.get()
                    .line.get()
                    ._is_interface.get()
                    .get_connected()[0]
                    .get()
                )
            )
        else:
            assert (
                led_indicator.resistor.get()
                .unnamed[1]
                .get()
                ._is_interface.get()
                .is_connected_to(
                    led_indicator.logic.get()
                    .line.get()
                    ._is_interface.get()
                    .get_connected()[0]
                    .get()
                )
            )
