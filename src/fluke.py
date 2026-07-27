import serial
from dataclasses import dataclass
from typing import Union
import flukeenums as fle


@dataclass
class MeasurementInfo():
    no: int
    valid: int
    source: int
    unit: int
    type: int
    pres: int
    resol: float

    def __str__(self):
        if self.valid != 1:
            return "Invalid measurement."
        
        return (
            f"{self.no.label}: {self.resol} "
            f"{self.unit.label} {self.type.name.replace('_', ' ')} "
            f"from {self.source.label} ({self.pres.name})"
        )

class FlukeSyntaxError(Exception):
    pass

class FlukeExecutionError(Exception):
    pass

class FlukeSynchronizationError(Exception):
    pass

class FlukeCommunicationError(Exception):
    pass

class Fluke:
    """
    Simple FLUKE 190 series ScopeMeter Python Control API
    by Egemen Bozkus

    Link to Fluke Programming Reference: https://media.fluke.com/d602147f-0db6-43c4-8d91-b10800c14f4e_original%20file.pdf

    Use query() for to send and read any command. See "def measure...()" preset methods at the bottom. 
    """

    def __init__(self, port: str):
        self.ser = serial.Serial(
            port=port,
            baudrate=1200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=True,
            timeout=2
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def send(self, cmd):
        packet = f"{cmd}\r".encode("ascii")
        self.ser.write(packet)

    def read_ack(self):
        ack = self.read_until_cr().decode("ascii")
        if ack == "1":
            raise FlukeSyntaxError(f"Ack returned {ack}: Syntax Error. Check your command syntax.")
        elif ack == "2":
            raise FlukeExecutionError(f"Ack returned {ack}: Execution Error. Data may be out of range or conflicting instrument settings")
        elif ack == "3":
            raise FlukeSynchronizationError(f"Ack returned {ack}: Synchronization Error.")
        elif ack == "4":
            raise FlukeCommunicationError(f"Ack returned {ack}: Communication Error.")

        return ack

    def read_until_cr(self):
        """FLUKE SMs use carrier return (<cr>) or \r instead of \n for new lines"""
        data = bytearray()

        while True:
            b = self.ser.read(1)

            if not b:
                break

            if b == b"\r":
                break

            data.extend(b)

        return bytes(data)

    def read_record(self):
        """Use like serial.readline()"""
        return self.read_until_cr().decode("ascii")

    def query(self,cmd):
        """Useful if you want to run your own command"""
        self.send(cmd)
        ack = self.read_ack()
        
        return self.read_record()

    def identify(self):
        return self.query("ID")

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def measure_all(self, mode):
        """
        Equivalent of sending just "QM" cmd to scopemeter.

        Reads all available measurements in form: 
        [[<no>,<valid>,<source>,<unit>,<type>,<pres>,<resol>], ...]

        Args: mode (str) Pass either "scope", "meter", or "trend"
        Returns: [MeasurementInfo, ...]
        """
        data = self.query("QM").split(',')

        mode_to_measurement = {
            "scope": fle.ScopeMeasurement,
            "meter": fle.MeterMeasurement,
            "trend": fle.TrendMeasurement,
        }[mode]

        res = []
        for i in range(0, len(data), 7):
            res.append(
                MeasurementInfo(
                    mode_to_measurement(int(data[i])), 
                    fle.MeasurementValidity(int(data[i+1])), 
                    fle.MeasurementSource(int(data[i+2])), 
                    fle.MeasurementUnit(int(data[i+3])), 
                    fle.MeasurementType(int(data[i+4])), 
                    fle.MeasurementPresentation(int(data[i+5])), 
                    float(data[i+6])
                )
            )

        return res
    
    def measure(self, *measurements: Union[int, fle.Measurement]) -> float | list[float]:
        """
        Sends "QM [<no>, ...]" cmd to scopemeter. 
        Accepts int or Measurement enum as inputs.
        Returns: Measurement value as a single float or list of float depending on input
        """
        ids = [int(m) for m in measurements]

        cmd = "QM " + ",".join(map(str, ids))
        response = self.query(cmd)

        values = [float(v) for v in response.split(",")]

        return values[0] if len(values) == 1 else values

    def query_print_png(self, screen_number: int = 0) -> bytes:
        """
        Sends "QP <screen_number>,11,B" cmd to scopemeter (QUERY PRINT) to request a PNG
        screen dump over the binary block-transfer protocol, and returns the reassembled
        PNG file bytes.

        Only PNG (<output_format> 11, block transfer mandatory) is currently supported.
        The other QP <output_format> values (Epson, LaserJet, DeskJet, PostScript,
        FBRLE2D) return raw "real printer" data via a different, non-block-transfer
        response and are not yet implemented.

        Args: screen_number: Screen image number to capture. 0 (default) is the active
            screen and the only value supported on most instruments.
        Returns: bytes containing the raw PNG file data.
        """
        cmd = f"QP {int(screen_number)},{int(fle.PrintFormat.PNG)},B"
        self.send(cmd)
        self.read_ack()

        return self._read_block_transfer()

    def save_screen_png(self, path: str, screen_number: int = 0):
        """
        Requests a PNG screen dump (see query_print_png()) and writes it to path.

        Args:
            path: File path to write the PNG image to.
            screen_number: Screen image number to capture. 0 (default) is the active screen.
        """
        data = self.query_print_png(screen_number)

        with open(path, "wb") as f:
            f.write(data)

    def _read_exact(self, n: int) -> bytes:
        """Reads exactly n raw bytes from the serial port, or raises if the instrument
        stops sending before n bytes arrive (read timeout)."""
        data = self.ser.read(n)
        if len(data) != n:
            raise FlukeCommunicationError(
                f"Expected {n} bytes but received {len(data)}: instrument stopped responding."
            )

        return data

    def _read_block_transfer(self) -> bytes:
        """Reads a QP binary block-transfer response (e.g. requested via block_transfer="B").

        Response syntax: <data_length>,<segment>{<segment>}
        Repeatedly requests and reassembles <segment> blocks until the last-block flag is
        set, verifying each block's checksum.
        """
        expected_length = self._read_block_transfer_length()

        data = bytearray()
        is_last = False

        while not is_last:
            block_data, is_last = self._read_print_block()
            data.extend(block_data)

        if len(data) != expected_length:
            raise FlukeCommunicationError(
                f"Block transfer length mismatch: expected {expected_length} bytes, got {len(data)}."
            )

        return bytes(data)

    def _read_block_transfer_length(self) -> int:
        """Reads the <data_length> = <digit>{<digit>} field, terminated by a comma."""
        digits = bytearray()

        while True:
            b = self._read_exact(1)

            if b.isdigit():
                digits.extend(b)
            elif b == b",":
                break
            else:
                raise FlukeCommunicationError(
                    f"Unexpected byte in block-transfer length field: {b!r}"
                )

        return int(digits.decode("ascii"))

    def _read_print_block(self) -> tuple[bytes, bool]:
        """Requests and reads one <segment> of a QP block-transfer response.

        <segment> = <ackn><cr>#0<block_header><block_length><block_data><check_sum><cr>

        Returns: (block_data, is_last_block)
        """
        self.send("0")  # segment_acknowledge: 0 = continue, request next segment
        self.read_ack()

        header = self._read_exact(5)
        if header[0:2] != b"#0":
            raise FlukeCommunicationError(
                f"Block transfer protocol error: expected '#0' block marker, got {header[0:2]!r}."
            )

        block_header = header[2]
        block_length = header[3] * 256 + header[4]
        is_last = bool(block_header & 0x80)

        block_data = self._read_exact(block_length)
        trailer = self._read_exact(2)  # <check_sum><cr>
        checksum = trailer[0]

        calculated_checksum = sum(block_data) % 256
        if calculated_checksum != checksum:
            self.send("2")  # segment_acknowledge: 2 = terminate transfer
            self.read_ack()
            raise FlukeCommunicationError(
                f"Block transfer checksum error: expected {checksum}, calculated {calculated_checksum}."
            )

        return block_data, is_last