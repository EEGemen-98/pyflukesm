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

    def __exit__(self):
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