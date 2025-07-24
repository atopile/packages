import faebryk.library._F as F  # noqa: F401
from faebryk.libs.units import P, dimensionless  # noqa: F401
from faebryk.core.module import Module  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.util import times  # noqa: F401
from faebryk.libs.units import Quantity


class ADBMS6830InputFilters(Module):
    def __init__(
        self,
        number_of_cells: int = 16,
        sense_filter_capacitance: Quantity = 100 * P.nF,
        sense_filter_resistance: Quantity = 200 * P.Ω,
        balance_filter_res: Quantity = 100 * P.nF,
        total_number_of_channels: int = 16,
    ):
        super().__init__()
        self.number_of_cells = number_of_cells
        self.sense_filter_capacitance = sense_filter_capacitance
        self.sense_filter_resistance = sense_filter_resistance
        self.total_number_of_channels = total_number_of_channels

    bleed_resistance = L.p_field(
        units=P.Ω
    )  # , likely_constrained=True, soft_set=L.Range(10 * P.Ω, 100 * P.Ω), tolerance_guess=1 * P.percent)

    @L.rt_field
    def cell_inputs(self) -> list[F.ElectricPower]:
        return times(self.number_of_cells, F.ElectricPower)

    @L.rt_field
    def sense_inputs(self) -> list[F.DifferentialPair]:
        return times(self.number_of_cells, F.DifferentialPair)

    @L.rt_field
    def balance_inputs(self) -> list[F.DifferentialPair]:
        return times(self.number_of_cells, F.DifferentialPair)

    class SenseFilter(Module):
        def __init__(
            self,
            number_of_cells: int = 16,
            sense_filter_resistance: Quantity = 200 * P.Ω,
            sense_filter_capacitance: Quantity = 10 * P.nF,
        ):
            super().__init__()
            self.number_of_cells = number_of_cells
            self.sense_filter_resistance = sense_filter_resistance
            self.sense_filter_capacitance = sense_filter_capacitance

        cell_power: F.ElectricPower
        sense_input: F.DifferentialPair

        sense_resistor: F.Resistor
        sense_capacitor: F.Capacitor

        filter_corner_frequency: Quantity

        def __preinit__(self):
            self.sense_resistor.resistance.alias_is(self.sense_filter_resistance)
            self.sense_capacitor.capacitance.alias_is(self.sense_filter_capacitance)
            self.filter_corner_frequencyalias_is(
                2 * P.π * self.sense_filter_resistance * self.sense_filter_capacitance
            )

            self.cell_power.hv.connect_via(self.sense_resistor, self.sense_input.p.line)
            self.sense_input.p.line.connect_via(
                self.sense_capacitor, self.sense_input.n.line
            )

    class BalanceFilter(Module):
        def __init__(
            self,
            number_of_cells: int = 16,
            balance_filter_resistance: Quantity = 15 * P.Ω,  # TODO: Calculate these
            balance_filter_capacitance: Quantity = 100 * P.nF,
        ):
            super().__init__()
            self.number_of_cells = number_of_cells
            self.balance_filter_resistance = balance_filter_resistance
            self.balance_filter_capacitance = balance_filter_capacitance

        cell_power: F.ElectricPower
        balance_input: F.DifferentialPair
        cap_bridge_connect: F.ElectricSignal

        top_balance_resistor: F.Resistor
        bottom_balance_resistor: F.Resistor
        differential_balance_capacitor: F.Capacitor
        bridge_capacitor: F.Capacitor

        balance_filter_capacitance: Quantity

        def __preinit__(self):
            self.top_balance_resistor.resistance.alias_is(
                self.balance_filter_resistance
            )
            self.bottom_balance_resistor.resistance.alias_is(
                self.balance_filter_resistance
            )
            self.differential_balance_capacitor.capacitance.alias_is(
                self.balance_filter_capacitance
            )
            self.bridge_capacitor.capacitance.alias_is(self.balance_filter_capacitance)

            self.cell_power.hv.connect_via(
                self.top_balance_resistor, self.balance_input.p.line
            )
            self.cell_power.lv.connect_via(
                self.bottom_balance_resistor, self.balance_input.n.line
            )
            self.balance_input.p.line.connect_via(
                self.differential_balance_capacitor, self.balance_input.n.line
            )
            self.balance_input.n.line.connect_via(
                self.bridge_capacitor, self.cap_bridge_connect.line
            )

    @L.rt_field
    def sense_filters(self) -> list[SenseFilter]:
        return times(self.number_of_cells, self.SenseFilter)

    @L.rt_field
    def balance_filters(self) -> list[BalanceFilter]:
        return times(self.number_of_cells, self.BalanceFilter)

    bottom_sense_filter: SenseFilter

    def __preinit__(self):
        # Stack all cell power interface in series
        # Connect input filters
        for idx, cell_input in enumerate(self.cell_inputs):
            cell_input.connect(self.sense_filters[idx].cell_power)
            self.sense_filters[idx].sense_input.connect(self.sense_inputs[idx])

            cell_input.connect(self.balance_filters[idx].cell_power)
            self.balance_filters[idx].balance_input.connect(self.balance_inputs[idx])

            if idx > 0:  # Connect bridge capacitor down the stack
                self.balance_filters[idx].cap_bridge_connect.connect(
                    self.balance_filters[idx - 1].balance_input.p
                )
            else:
                self.balance_filters[idx].cap_bridge_connect.line.connect(
                    self.cell_inputs[0].lv
                )

        # Connect Bottom of Stack to GND with additional sense filter
        self.bottom_sense_filter.cell_power.hv.connect(self.cell_inputs[0].lv)
        self.bottom_sense_filter.sense_input.p.line.connect(self.sense_inputs[0].n.line)
        self.bottom_sense_filter.sense_input.n.line.connect(self.cell_inputs[0].lv)

        # Depopulated channels
        number_of_depopulated_channels = (
            self.total_number_of_channels - self.number_of_cells
        )
        if number_of_depopulated_channels > 0:
            depop_resistor = self.add(F.Resistor())
            depop_resistor.resistance.alias_is(1 * P.kΩ)
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
