# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P
from faebryk.core.parameter import And, IsSubset
from faebryk.libs.util import groupby


class ResistanceMapper(Module):
    """
    This helper module will map the configuration resistor resitance to/from:
    - input current limit [100mA, 500mA, 1100mA]
    - battery voltage limit high
    - battery voltage limit low
    """

    resistor: F.Resistor
    input_current_limit = L.p_field(units=P.A)
    battery_voltage_limit_low = L.p_field(units=P.V)
    battery_voltage_limit_high = L.p_field(units=P.V)

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(*self.resistor.unnamed)

    def __preinit__(self):
        VALID_CURRENT_LIMITS = (
            100 * P.mA,
            500 * P.mA,
            1100 * P.mA,
        )
        self.input_current_limit.constrain_subset(
            L.RangeWithGaps(VALID_CURRENT_LIMITS)  # type: ignore
        )

        TABLE = [
            (130, 500, 4.1, 3.0),
            (100, 1100, 4.1, 3.0),
            (75, 500, 4.4, 3.0),
            (56, 1100, 4.4, 3.0),
            (43, 500, 4.35, 3.0),
            (33, 1100, 4.35, 3.0),
            (24, 100, 4.2, 3.0),
            (18, 500, 4.2, 3.0),
            (13, 1100, 4.2, 3.0),
            (9.1, 500, 4.05, 3.0),
            (6.8, 1100, 4.05, 3.0),
            (5.1, 1100, 3.65, 2.0),
            (3.6, 500, 3.6, 2.0),
            (2.4, 1100, 3.6, 2.0),
        ]
        R_TOLERANCE = 1 * P.percent

        # r kOhm, iLim mA, BatRegHigh V, BatRegLow V
        TABLE_UNITS = [
            (
                L.Range.from_center_rel(r * P.kohm, R_TOLERANCE),
                i * P.mA,
                v * P.V,
                low * P.V,
            )
            for r, i, v, low in TABLE
        ]

        # only toleranced nomimal resistors allowed
        self.resistor.resistance.constrain_subset(
            L.RangeWithGaps(*{k[0] for k in TABLE_UNITS})  # type: ignore
        )

        # R -> iLim, BatRegHigh, BatRegLow
        self.resistor.resistance.operation_switch_case_subset(
            (
                r,
                And(
                    IsSubset(self.input_current_limit, i),
                    IsSubset(self.battery_voltage_limit_high, v_high),
                    IsSubset(self.battery_voltage_limit_low, v_low),
                ),
            )
            for r, i, v_high, v_low in TABLE_UNITS
        )

        # iLim -> R
        iLim_R_mapping: dict[L.Range, L.RangeWithGaps] = {
            i: L.RangeWithGaps(*{r for r, _, _, _ in ks})
            for i, ks in groupby(TABLE_UNITS, key=lambda x: x[1]).items()
        }
        self.input_current_limit.constrain_mapping(
            self.resistor.resistance,
            iLim_R_mapping,
        )

        # BatRegHigh -> R
        BatRegHigh_R_mapping: dict[L.Range, L.RangeWithGaps] = {
            v: L.RangeWithGaps(*{r for r, _, _, _ in ks})
            for v, ks in groupby(TABLE_UNITS, key=lambda x: x[2]).items()
        }
        self.battery_voltage_limit_high.constrain_mapping(
            self.resistor.resistance,
            BatRegHigh_R_mapping,
        )

        # BatRegLow -> R
        BatRegLow_R_mapping: dict[L.Range, L.RangeWithGaps] = {
            v: L.RangeWithGaps(*{r for r, _, _, _ in ks})
            for v, ks in groupby(TABLE_UNITS, key=lambda x: x[3]).items()
        }
        self.battery_voltage_limit_low.constrain_mapping(
            self.resistor.resistance,
            BatRegLow_R_mapping,
        )
