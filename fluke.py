import serial

class Fluke:
    """
    Simple FLUKE 190 series ScopeMeter Python Control API
    by Egemen Bozkus

    Link to Fluke Programming Reference: https://media.fluke.com/d602147f-0db6-43c4-8d91-b10800c14f4e_original%20file.pdf

    Use query() for to send and read any command. I also have some preset methods for common commands like
    measure_frequency() and measure_Vrms().
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
        """Basically serial.readline() but looks for \r instead of \n"""
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
        return self.read_until_cr().decode("ascii")

    def query(self,cmd):
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

    def measure_frequency(self):
        return float(self.query("QM 21"))

    def measure_Vrms(self):
        return float(self.query("QM 11"))