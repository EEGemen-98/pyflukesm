from enum import IntEnum

"""
    Enums for QM codes
    See pg 29 in programming reference
"""

class ScopeMeasurement(IntEnum):
    READING_1 = 11
    READING_2 = 21

    CURSOR_1_ABS_AMP = 31
    CURSOR_2_ABS_AMP = 41

    CURSOR_ABS_AMP_MAX = 53
    CURSOR_ABS_AMP_AVG = 54
    CURSOR_ABS_AMP_MIN = 55

    CURSOR_RELATIVE_AMP_DELTA_V = 61
    CURSOR_RELATIVE_AMP_DELTA_T = 71

    @property
    def label(self):
        return {
            self.READING_1: "Reading 1",
            self.READING_2: "Reading 2",
            self.CURSOR_1_ABS_AMP: "Cursor 1 Abs Ampl",
            self.CURSOR_2_ABS_AMP: "Cursor 2 Abs Ampl",
            self.CURSOR_ABS_AMP_MAX: "Cursor Abs Max Ampl",
            self.CURSOR_RELATIVE_AMP_DELTA_V: "Cursor Relative Ampl Delta V",
            self.CURSOR_RELATIVE_AMP_DELTA_T: "Cursor Relative Ampl Delta T"
        }[self]


class MeterMeasurement(IntEnum):
    # Meter mode only
    METER_ABSOLUTE = 11
    METER_RELATIVE = 19

class TrendMeasurement(IntEnum):
    # Trend plot mode
    TREND_READING_1 = 11
    TREND_READING_2 = 21



class MeasurementValidity(IntEnum):
    INVALID = 0
    VALID = 1

class MeasurementSource(IntEnum):
    INPUT_A = 1
    INPUT_B = 2
    EXTERNAL_INPUT = 3

    A_OVER_B_OR_M = 12
    B_OVER_A = 21

    @property
    def label(self):
        return {
            self.INPUT_A: "Input A",
            self.INPUT_B: "Input B",
            self.EXTERNAL_INPUT: "External Input",
            self.A_OVER_B_OR_M: "A/B",
            self.B_OVER_A: "B/A"
        }[self]

class MeasurementUnit(IntEnum):
    NONE = 0

    VOLT = 1
    AMPERE = 2
    OHM = 3
    WATT = 4
    FARAD = 5
    KELVIN = 6

    SECOND = 7
    HOUR = 8
    DAY = 9

    HERTZ = 10
    DEGREE = 11

    CELSIUS = 12
    FAHRENHEIT = 13

    PERCENT = 14

    DBM_50_OHM = 15
    DBM_600_OHM = 16

    DB_VOLT = 17
    DB_AMPERE = 18
    DB_WATT = 19

    VAR = 20
    VA = 21

    @property
    def label(self):
        return {
            self.NONE: "N/A",
            self.VOLT: "V",
            self.AMPERE: "A",
            self.OHM: "Ω",
            self.WATT: "W",
            self.FARAD: "F",
            self.KELVIN: "K",
            self.SECOND: "s",
            self.HOUR: "h",
            self.DAY: "d",
            self.HERTZ: "Hz",
            self.DEGREE: "º",
            self.CELSIUS: "ºC",
            self.FAHRENHEIT: "ºF",
            self.PERCENT: "%",
            self.DBM_50_OHM: "dBm (50Ω)",
            self.DBM_600_OHM: "dBm (600Ω)",
            self.DB_VOLT: "dBV",
            self.DB_AMPERE: "dBA",
            self.DB_WATT: "dBW",
            self.VAR: "Var",
            self.VA: "VA"
        }[self]

class MeasurementType(IntEnum):
    NONE = 0

    MEAN = 1
    RMS = 2
    TRUE_RMS = 3

    PEAK_TO_PEAK = 4
    PEAK_MAXIMUM = 5
    PEAK_MINIMUM = 6

    CREST_FACTOR = 7

    PERIOD = 8

    DUTY_CYCLE_NEGATIVE = 9
    DUTY_CYCLE_POSITIVE = 10

    FREQUENCY = 11

    PULSE_WIDTH_NEGATIVE = 12
    PULSE_WIDTH_POSITIVE = 13

    PHASE = 14

    DIODE = 15
    CONTINUITY = 16

    # 17 intentionally unused

    REACTIVE_POWER = 18
    APPARENT_POWER = 19
    REAL_POWER = 20

    HARMONIC_REACTIVE_POWER = 21
    HARMONIC_APPARENT_POWER = 22
    HARMONIC_REAL_POWER = 23
    HARMONIC_RMS = 24

    DISPLACEMENT_POWER_FACTOR = 25
    TOTAL_POWER_FACTOR = 26

    TOTAL_HARMONIC_DISTORTION = 27
    THD_FUNDAMENTAL = 28

    K_FACTOR_EUROPE = 29
    K_FACTOR_US = 30

    LINE_FREQUENCY = 31

    VAC_PWM = 32

    RISE_TIME = 33
    FALL_TIME = 34


class MeasurementPresentation(IntEnum):
    ABSOLUTE = 0
    RELATIVE = 1
    LOGARITHMIC = 2
    LINEAR = 3
    FAHRENHEIT = 4
    CELSIUS = 5