import pytest


class FakeSerial:
    """
    Mock Serial class. Records every write() and replays
    queued <cr>-terminated ASCII records on read(), one byte at a time,
    mirroring Fluke.read_until_cr().
    """

    def __init__(self, *args, **kwargs):
        self.is_open = True
        self.sent = []
        self._rx = bytearray()

    def queue(self, *records: str):
        """Queue one or more records to be read back in order, e.g. queue('0', '3.30')."""
        for record in records:
            self._rx.extend(record.encode("ascii") + b"\r")

    def write(self, data: bytes):
        self.sent.append(data)

    def read(self, size: int = 1) -> bytes:
        if not self._rx:
            return b""
        chunk = bytes(self._rx[:size])
        del self._rx[:size]
        return chunk

    def close(self):
        self.is_open = False


@pytest.fixture
def fake_serial(monkeypatch):
    """
    Monkeypatch Serial with our FakeSerial. 
    Collect but ignore any args.
    """
    fs = FakeSerial()
    monkeypatch.setattr("serial.Serial", lambda *args, **kwargs: fs)
    return fs


@pytest.fixture
def scope(fake_serial):
    """Instantiates mock Fluke object with fake serial port."""
    from fluke import Fluke

    return Fluke("FAKE")
