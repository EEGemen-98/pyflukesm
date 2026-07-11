# pyflukesm

Simple and easy to use Python API for controlling the FLUKE 190 series ScopeMeter over a serial connection.

Solo project, WIP. So far measurement queries are working, see usage below.

FLUKE Programming Guide: https://media.fluke.com/d602147f-0db6-43c4-8d91-b10800c14f4e_original%20file.pdf

(I'm not affiliated with FLUKE in any way. Just doing this for fun.)

## Installation

Requires [pyserial](https://pypi.org/project/pyserial/):

```bash
pip install pyserial
```

Then drop `fluke.py` and `flukeenums.py` into your project.

## Quick start

```python
from fluke import Fluke
import flukeenums as fle

scope = Fluke("COM3")  # or "/dev/ttyUSB0" on Linux/Mac

print(scope.identify())
print(scope.measure(fle.ScopeMeasurement.READING_1))

scope.close()
```

`Fluke` also works as a context manager, which closes the serial port for you automatically:

```python
with Fluke("COM3") as scope:
    print(scope.identify())
```

## The `Fluke` class

`Fluke(port: str)` opens a serial connection to the ScopeMeter at 1200 baud, 8N1, with software flow control (`xonxoff=True`) and a 2 second read timeout — these match the FLUKE 190 series' fixed RS-232 settings, so you only need to supply the port.

```python
scope = Fluke("COM3")
```

Every command you send goes through the same request/acknowledge cycle the instrument expects: a command is written, a one-character ACK is read back and checked for errors, then the actual response (if any) is read as a `<cr>`-terminated record. All of the methods below (`query`, `identify`, `measure_all`, `measure`) are built on top of this cycle, so you rarely need to touch the lower-level `send()` / `read_ack()` / `read_record()` helpers directly.

If the instrument returns a non-zero ACK, `Fluke` raises one of:

| Exception | ACK | Meaning |
|---|---|---|
| `FlukeSyntaxError` | 1 | Command syntax is invalid |
| `FlukeExecutionError` | 2 | Data out of range or conflicting instrument settings |
| `FlukeSynchronizationError` | 3 | Synchronization error |
| `FlukeCommunicationError` | 4 | Communication error |

Call `scope.close()` when you're done (or use the `with` statement, which does this for you).

### `query(cmd)`

Sends a raw command string to the ScopeMeter and returns its response as a string. Use this for any command not covered by a dedicated method — see the Programming Guide linked above for the full command set.

```python
scope.query("ID")          # "FLUKE,199C,ABC123,V1.00"
scope.query("QM")          # raw comma-separated measurement dump, see measure_all()
scope.query("MEASURE?")    # example of an arbitrary command
```

`query()` raises `FlukeSyntaxError`, `FlukeExecutionError`, `FlukeSynchronizationError`, or `FlukeCommunicationError` if the instrument NAKs the command. Not every command in the Programming Guide has been tested, so use it with care.

### `measure_all(mode)`

Equivalent to sending the `QM` command with no arguments: asks the instrument for *every* measurement it currently has available, and parses the response into a list of `MeasurementInfo` objects instead of a raw comma-separated string.

```python
Args:
    mode (str): "scope", "meter", or "trend" — selects which Measurement
                enum (ScopeMeasurement / MeterMeasurement / TrendMeasurement)
                is used to decode each measurement's "no" field.

Returns:
    list[MeasurementInfo]
```

Example:

```python
readings = scope.measure_all("scope")

for r in readings:
    print(r)
```

```
Reading 1: 3.30 V MEAN from Input A (ABSOLUTE)
Reading 2: 0.02 V RMS from Input A (ABSOLUTE)
Cursor 1 Abs Ampl: 1.20 V PEAK MAXIMUM from Input B (ABSOLUTE)
```

Each `MeasurementInfo` has the fields below (decoded from the instrument's `<no>,<valid>,<source>,<unit>,<type>,<pres>,<resol>` tuple). Note that everything except `resol` is a **typed Enum** from `flukeenums.py`, not a raw int:

| Field | Type | Description |
|---|---|---|
| `no` | `ScopeMeasurement` \| `MeterMeasurement` \| `TrendMeasurement` | Which measurement slot this is (depends on `mode`) |
| `valid` | `MeasurementValidity` | Whether the measurement is currently valid |
| `source` | `MeasurementSource` | Input A, Input B, external input, A/B, etc. |
| `unit` | `MeasurementUnit` | Volt, Ampere, Ohm, Hertz, etc. |
| `type` | `MeasurementType` | Mean, RMS, peak-to-peak, frequency, etc. |
| `pres` | `MeasurementPresentation` | Absolute, relative, logarithmic, etc. |
| `resol` | `float` | The measured value |

`MeasurementInfo` has a friendly `__str__` (used in the example above), and prints `"Invalid measurement."` if `valid` is not `MeasurementValidity.VALID`.

```python
for r in scope.measure_all("meter"):
    if r.valid == fle.MeasurementValidity.VALID:
        print(f"{r.type.name}: {r.resol}{r.unit.label}")
```

### `measure(*measurements)`

Sends `QM <no>[,<no>...]` to request one or more *specific* measurement values by number, and returns just the numeric value(s) — no metadata. This is the fast path when you already know which measurement(s) you want (e.g. polling a single channel in a loop) and don't need `measure_all()`'s full decode.

```python
Args:
    *measurements (int | flukeenums.Measurement): one or more measurement
        numbers, either as plain ints or as Measurement enum members
        (e.g. ScopeMeasurement.READING_1).

Returns:
    float if a single measurement was requested,
    list[float] if multiple measurements were requested.
```

Single measurement:

```python
voltage = scope.measure(fle.ScopeMeasurement.READING_1)
print(voltage)  # 3.3
```

Multiple measurements in one round trip:

```python
v1, v2 = scope.measure(fle.ScopeMeasurement.READING_1, fle.ScopeMeasurement.READING_2)
```

Plain ints work too, if you'd rather look up the number directly from the Programming Guide:

```python
scope.measure(11, 21)
```

### Other methods

- `identify()` — shorthand for `query("ID")`, returns the instrument's identification string.
- `close()` — closes the serial connection. Called automatically if using `Fluke` as a context manager.

## Measurement enums (`flukeenums.py`)

Measurement numbers, units, types, etc. are defined as `IntEnum`s so you get autocomplete and readable code instead of magic numbers. See page 29 of the Programming Reference for the full table these are derived from.

- `ScopeMeasurement`, `MeterMeasurement`, `TrendMeasurement` — mode-specific measurement slot numbers (used for the `no` field / passed to `measure()`)
- `MeasurementValidity` — `INVALID` / `VALID`
- `MeasurementSource` — `INPUT_A`, `INPUT_B`, `EXTERNAL_INPUT`, `A_OVER_B_OR_M`, `B_OVER_A`
- `MeasurementUnit` — `VOLT`, `AMPERE`, `OHM`, `HERTZ`, `CELSIUS`, etc.
- `MeasurementType` — `MEAN`, `RMS`, `TRUE_RMS`, `PEAK_TO_PEAK`, `FREQUENCY`, `DUTY_CYCLE_POSITIVE`, etc.
- `MeasurementPresentation` — `ABSOLUTE`, `RELATIVE`, `LOGARITHMIC`, `LINEAR`, `FAHRENHEIT`, `CELSIUS`

`ScopeMeasurement`, `MeasurementSource`, and `MeasurementUnit` also expose a `.label` property with a human-readable string (used by `MeasurementInfo.__str__`), e.g. `MeasurementUnit.VOLT.label == "V"`.
