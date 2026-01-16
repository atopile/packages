import math
from faebryk.core.parameter import Quantity_Interval
from faebryk.library.FilterElectricalLC import FilterElectricalLC
import faebryk.library._F as F  # noqa: F401
from faebryk.libs.units import P, dimensionless  # noqa: F401
from faebryk.core.module import Module  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.util import times  # noqa: F401
from faebryk.libs.units import Quantity
from faebryk.libs.sets.quantity_sets import Quantity_Interval_Disjoint


class SenseFilter(Module):
    def __init__(
        self,
        sense_filter_resistance: Quantity_Interval = L.Range.from_center_rel(
            200 * P.Ω, 1 * P.percent
        ),
        sense_filter_capacitance: Quantity_Interval = L.Range.from_center_rel(
            10 * P.nF, 20 * P.percent
        ),
    ):
        super().__init__()
        self.sense_filter_resistance = sense_filter_resistance
        self.sense_filter_capacitance = sense_filter_capacitance

    cell_power: F.ElectricPower
    sense_input: F.DifferentialPair

    @L.rt_field
    def sense_filter(self):
        return F.FilterElectricalRC.hardcoded_rc(
            self.sense_filter_resistance,
            self.sense_filter_capacitance,
        )

    def __preinit__(self):
        self.cell_power.hv.connect_via(
            self.sense_filter.resistor, self.sense_input.p.line
        )
        self.sense_input.p.line.connect_via(
            self.sense_filter.capacitor, self.sense_input.n.line
        )


class BalanceFilter(Module):
    def __init__(
        self,
        bleed_resistance_target: float = 20 * P.ohms,
        bleed_filter_capacitance: Quantity_Interval = L.Range.from_center_rel(
            10 * P.nF, 20 * P.percent
        ),
    ):
        super().__init__()
        self.bleed_resistance_target = bleed_resistance_target
        self.bleed_filter_capacitance = bleed_filter_capacitance

    cell_power: F.ElectricPower
    balance_input: F.DifferentialPair
    cap_bridge_connect: F.ElectricSignal  # Connect to cell below, transients to gnd

    @L.rt_field
    def top_balance_filter(self):
        bleed_resistance = L.Range.from_center_rel(
            self.bleed_resistance_target,
            5 * P.percent,
        )
        return F.FilterElectricalRC.hardcoded_rc(
            bleed_resistance,
            self.bleed_filter_capacitance,
        )

    @L.rt_field
    def bottom_balance_filter(self):
        bleed_resistance = L.Range.from_center_rel(
            self.bleed_resistance_target,
            5 * P.percent,
        )
        return F.FilterElectricalRC.hardcoded_rc(
            bleed_resistance,
            self.bleed_filter_capacitance,
        )

    def __preinit__(self):
        self.top_balance_filter.resistor.max_power.constrain_ge(
            (4.25 / 2 * P.V) * (4.25 / 2 * P.V) / (self.bleed_resistance_target)
        )
        self.bottom_balance_filter.resistor.max_power.constrain_ge(
            (4.25 / 2 * P.V) * (4.25 / 2 * P.V) / (self.bleed_resistance_target)
        )
        self.cell_power.hv.connect_via(
            self.top_balance_filter.resistor, self.balance_input.p.line
        )
        self.cell_power.lv.connect_via(
            self.bottom_balance_filter.resistor, self.balance_input.n.line
        )
        self.balance_input.p.line.connect_via(
            self.top_balance_filter.capacitor, self.balance_input.n.line
        )
        self.balance_input.n.line.connect_via(
            self.bottom_balance_filter.capacitor, self.cap_bridge_connect.line
        )


class ADBMS6830InputFilters(Module):
    """
    Filters between the cell connections and the primary and secondary sense pins of the ADBMS6830.

    :param number_of_cells: Number of battery cells in the stack
    :param sense_filter_resistance: Resistance of the sense filter
    :param sense_filter_capacitance: Capacitance of the sense filter
    :param max_balance_current: Maximum balance current, used to calculate balance resistor values
    :param total_number_of_channels: Total number of channels available on ASIC, unused channels are depopulated

    Balance Filters: f(max_balance_current, sense_filter_corner_frequency)
        Values calculated from maximum balance current and sense filter corner frequency
    """

    def __init__(
        self,
        number_of_cells: int = 6,
        sense_filter_resistance_ohms: int = 200,
        sense_filter_capacitance_nF: int = 10,
        max_balance_current_mA: float = 200,
        total_number_of_channels: int = 16,
    ):
        super().__init__()
        self.number_of_cells = number_of_cells
        self.sense_filter_resistance = L.Range.from_center_rel(
            sense_filter_resistance_ohms * P.Ω, 1 * P.percent
        )
        self.sense_filter_capacitance = L.Range.from_center_rel(
            sense_filter_capacitance_nF * P.nF, 20 * P.percent
        )
        self.max_balance_current = max_balance_current_mA * P.mA
        self.total_number_of_channels = total_number_of_channels

    @L.rt_field
    def cell_inputs(self) -> list[F.ElectricPower]:
        return times(self.number_of_cells, F.ElectricPower)

    @L.rt_field
    def sense_inputs(self) -> list[F.DifferentialPair]:
        return times(self.total_number_of_channels, F.DifferentialPair)

    @L.rt_field
    def balance_inputs(self) -> list[F.DifferentialPair]:
        return times(self.total_number_of_channels, F.DifferentialPair)

    @L.rt_field
    def sense_filters(self) -> list[SenseFilter]:
        return times(
            self.number_of_cells,
            lamb=lambda: SenseFilter(
                self.sense_filter_resistance, self.sense_filter_capacitance
            ),
        )

    @L.rt_field
    def balance_filters(self) -> list[BalanceFilter]:
        bleed_resistance_target = ((4.25 * P.V) / self.max_balance_current) / 2
        bleed_filter_capacitance = L.Range.from_center_rel(
            1 / (bleed_resistance_target * (2 * math.pi) * (80 * P.kHz)),
            20 * P.percent,
        )
        return times(
            self.number_of_cells,
            lamb=lambda: BalanceFilter(
                bleed_resistance_target, bleed_filter_capacitance
            ),
        )

    """
    Bottom sense filter, used to connect the bottom of the first cell to the lowest
    ADC channel - side and filter transients to gnd
    """

    def __preinit__(self):
        # self.bleed_resistance_target.alias_is(
        #     ((4.25 * P.V) / self.max_balance_current) / 2
        # )
        # Calculate balance resistance value based on max balance current
        for idx, cell_input in enumerate(self.cell_inputs):
            # Set filter component values
            # self.sense_filters[idx].sense_filter.hardcoded_rc(
            #     L.Range.from_center_rel(10 * P.ohms, 5 * P.percent),
            #     L.Range.from_center_rel(47 * P.nF, 20 * P.percent),
            # )
            # self.balance_filters[idx].top_balance_filter.hardcoded_rc(
            #     L.Range.from_center_rel(10 * P.ohms, 5 * P.percent),
            #     L.Range.from_center_rel(47 * P.nF, 20 * P.percent),
            # )
            # self.balance_filters[idx].bottom_balance_filter.hardcoded_rc(
            #     L.Range.from_center_rel(10 * P.ohms, 5 * P.percent),
            #     L.Range.from_center_rel(47 * P.nF, 20 * P.percent),
            # )

            cell_input.connect(self.sense_filters[idx].cell_power)
            self.sense_filters[idx].sense_input.connect(self.sense_inputs[idx])

            cell_input.connect(self.balance_filters[idx].cell_power)
            self.balance_filters[idx].balance_input.connect(self.balance_inputs[idx])

            if idx > 0:
                # Connect bridge capacitor down the stack
                self.balance_filters[idx].cap_bridge_connect.connect(
                    self.balance_filters[idx - 1].balance_input.p
                )
                # Connect cell stack together
                self.cell_inputs[idx].lv.connect(self.cell_inputs[idx - 1].hv)
            else:
                self.balance_filters[idx].cap_bridge_connect.line.connect(
                    self.cell_inputs[0].lv
                )

        # Connect Bottom of Stack to GND with additional sense filter
        self.bottom_sense_filter = self.add(
            SenseFilter(self.sense_filter_resistance, self.sense_filter_capacitance)
        )
        self.bottom_sense_filter.cell_power.hv.connect(self.cell_inputs[0].lv)
        self.bottom_sense_filter.sense_input.p.line.connect(self.sense_inputs[0].n.line)
        self.bottom_sense_filter.sense_input.n.line.connect(self.cell_inputs[0].lv)

        """
        If there are any depopulated channels, connect both the sense and
        balance inputs to the top of the stack through a 1kohm resistor
        """
        number_of_depopulated_channels = (
            self.total_number_of_channels - self.number_of_cells
        )
        if number_of_depopulated_channels > 0:
            depop_resistor = self.add(F.Resistor())
            depop_resistor.resistance.constrain_subset(
                L.Range.from_center_rel(1 * P.kΩ, 1 * P.percent)
            )
            for idx in range(number_of_depopulated_channels):
                self.sense_inputs[
                    self.total_number_of_channels - 1 - idx
                ].p.line.connect_via(
                    depop_resistor,
                    self.cell_inputs[self.number_of_cells - 1].hv,
                )
                self.sense_inputs[
                    self.total_number_of_channels - 1 - idx
                ].n.line.connect_via(
                    depop_resistor,
                    self.cell_inputs[self.number_of_cells - 1].hv,
                )
                self.balance_inputs[
                    self.total_number_of_channels - 1 - idx
                ].p.line.connect_via(
                    depop_resistor,
                    self.cell_inputs[self.number_of_cells - 1].hv,
                )
                self.balance_inputs[
                    self.total_number_of_channels - 1 - idx
                ].n.line.connect_via(
                    depop_resistor,
                    self.cell_inputs[self.number_of_cells - 1].hv,
                )
