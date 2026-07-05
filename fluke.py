import serial
from enum import Enum
from dataclasses import dataclass


class Measurement(Enum):
    """
    Enums for QM <no>
    See pg 29 in programming reference
    """
    READING_1 = 11
    READING_2 = 21
    CURSOR_1_ABS_AMP = 31
    CURSOR_2_ABS_AMP = 41
    CURSOR_ABS_AMP_MAX = 53
    CURSOR_ABS_AMP_AVG = 54
    CURSOR_ABS_AMP_MIN = 55
    CURSOR_RELATIVE_AMP_DELTA_V = 61
    CURSOR_RELATIVE_AMP_DELTA_T = 71

@dataclass
class MeasurementInfo:
    no: int
    valid: int
    source: int
    unit: int
    type: int
    pres: int
    resol: float

    #def __str__(self):
     #   return f""

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

    def __exit__(self):
        self.close()

    def send(self, cmd):
        packet = f"{cmd}\r".encode("ascii")
        self.ser.write(packet)

    def read_ack(self):
        ack = self.ser.readline()
        print("ACK:", repr(ack))
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
        ack = self.read_record()

        if ack != "0":
            raise Exception(f"Scope returned ACK {ack}")
        
        return self.read_record()

    def identify(self):
        return self.query("ID")

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def measure_all(self):
        """
        Reads all available measurements in form: 
        [[<no>,<valid>,<source>,<unit>,<type>,<pres>,<resol>], ...]

        Returns: [MeasurementInfo, ...]
        """
        data = self.query("QM").split(',')
        print(data)

        res = []
        for i in range(0, len(data), 7):
            res.append(
                MeasurementInfo(
                    int(data[i]), 
                    int(data[i+1]), 
                    int(data[i+2]), 
                    int(data[i+3]), 
                    int(data[i+4]), 
                    int(data[i+5]), 
                    float(data[i+6])
                )
            )

        return res

    def measure_reading1(self):
        """Read measurement 1"""
        return float(self.query("QM 11"))

    def measure_reading2(self):
        """Read measurement 2"""
        return float(self.query("QM 21"))

    def measure_cursor1_abs_amp(self):
        """Read cursor 1's absolute amplitude"""
        return float(self.query("QM 31"))

    def measure_cursor2_abs_amp(self):
        """Read cursor 2's absolute amplitude"""
        return float(self.query("QM 41"))

    def measure_cursor_abs_max_amp(self):
        """Read cursor absolute max amplitude"""
        return float(self.query("QM 53"))

    def measure_cursor_abs_avg_amp(self):
        """Read cursor absolute average amplitude"""
        return float(self.query("QM 54"))

    def measure_cursor_abs_min_amp(self):
        """Read cursor absolute minimum amplitude"""
        return float(self.query("QM 55"))

    def measure_cursor_rel_deltav_amp(self):
        """Read cursor relative delta V amplitude"""
        return float(self.query("QM 61"))

    def measure_cursor_rel_deltat_amp(self):
        """Read cursor relative delta T amplitude"""
        return float(self.query("QM 71"))
