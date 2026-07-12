import pytest

import flukeenums as fle
from fluke import FlukeSyntaxError

"""
Regression Test Suite. Not tests for real usage of scopemeter.
"""

def test_measure_single_value(scope, fake_serial):
    # Receive ACK: 0 with measurement '3.30'
    fake_serial.queue("0", "3.30")

    result = scope.measure(fle.ScopeMeasurement.READING_1)

    assert result == 3.30
    assert fake_serial.sent == [b"QM 11\r"]


def test_measure_multiple_values(scope, fake_serial):
    fake_serial.queue("0", "3.30,0.02")

    result = scope.measure(fle.ScopeMeasurement.READING_1, fle.ScopeMeasurement.READING_2)

    assert result == [3.30, 0.02]
    assert fake_serial.sent == [b"QM 11,21\r"]


def test_measure_accepts_plain_ints(scope, fake_serial):
    fake_serial.queue("0", "3.30")

    result = scope.measure(11)

    assert result == 3.30


def test_measure_all_scope_mode(scope, fake_serial):
    fake_serial.queue("0", "11,1,1,1,1,0,3.30")

    [info] = scope.measure_all("scope")

    assert info.no == fle.ScopeMeasurement.READING_1
    assert info.valid == fle.MeasurementValidity.VALID
    assert info.source == fle.MeasurementSource.INPUT_A
    assert info.unit == fle.MeasurementUnit.VOLT
    assert info.type == fle.MeasurementType.MEAN
    assert info.pres == fle.MeasurementPresentation.ABSOLUTE
    assert info.resol == 3.30


def test_measure_all_parses_multiple_records(scope, fake_serial):
    fake_serial.queue("0", "11,1,1,1,1,0,3.30,21,1,1,2,2,0,0.02")

    readings = scope.measure_all("scope")

    assert len(readings) == 2
    assert readings[0].no == fle.ScopeMeasurement.READING_1
    assert readings[1].no == fle.ScopeMeasurement.READING_2
    assert readings[1].unit == fle.MeasurementUnit.AMPERE


def test_query_raises_on_syntax_error(scope, fake_serial):
    fake_serial.queue("1")

    with pytest.raises(FlukeSyntaxError):
        scope.query("BOGUS")
