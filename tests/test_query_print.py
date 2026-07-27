import pytest

from fluke import FlukeCommunicationError


def make_segment(block_data: bytes, is_last: bool, checksum: int = None) -> bytes:
    """Builds a raw <segment> = #0<block_header><block_length><block_data><check_sum><cr>."""
    header = 0x80 if is_last else 0x00
    length = len(block_data)
    if checksum is None:
        checksum = sum(block_data) % 256

    return (
        b"#0"
        + bytes([header, length // 256, length % 256])
        + block_data
        + bytes([checksum])
        + b"\r"
    )


def test_query_print_png_reassembles_segments(scope, fake_serial):
    fake_serial.queue("0")  # ack for QP command
    fake_serial._rx.extend(b"7,")  # data_length

    fake_serial._rx.extend(b"0\r")  # ack for segment_acknowledge "0"
    fake_serial._rx.extend(make_segment(b"ABCDE", is_last=False))

    fake_serial._rx.extend(b"0\r")  # ack for segment_acknowledge "0"
    fake_serial._rx.extend(make_segment(b"XY", is_last=True))

    result = scope.query_print_png()

    assert fake_serial.sent == [b"QP 0,11,B\r", b"0\r", b"0\r"]
    assert result == b"ABCDEXY"


def test_query_print_png_single_segment(scope, fake_serial):
    fake_serial.queue("0")
    fake_serial._rx.extend(b"3,")

    fake_serial._rx.extend(b"0\r")
    fake_serial._rx.extend(make_segment(b"PNG", is_last=True))

    result = scope.query_print_png()

    assert result == b"PNG"


def test_query_print_png_uses_screen_number(scope, fake_serial):
    fake_serial.queue("0")
    fake_serial._rx.extend(b"0,")
    fake_serial._rx.extend(b"0\r")
    fake_serial._rx.extend(make_segment(b"", is_last=True))

    scope.query_print_png(screen_number=2)

    assert fake_serial.sent[0] == b"QP 2,11,B\r"


def test_query_print_png_checksum_error_terminates(scope, fake_serial):
    fake_serial.queue("0")  # ack for QP command
    fake_serial._rx.extend(b"5,")  # data_length

    fake_serial._rx.extend(b"0\r")  # ack for segment_acknowledge "0"
    fake_serial._rx.extend(make_segment(b"ABCDE", is_last=True, checksum=0))
    fake_serial._rx.extend(b"0\r")  # ack for the "2" terminate we send on error

    with pytest.raises(FlukeCommunicationError):
        scope.query_print_png()

    assert fake_serial.sent == [b"QP 0,11,B\r", b"0\r", b"2\r"]


def test_query_print_png_length_mismatch(scope, fake_serial):
    fake_serial.queue("0")  # ack for QP command
    fake_serial._rx.extend(b"99,")  # declared length does not match actual data

    fake_serial._rx.extend(b"0\r")  # ack for segment_acknowledge "0"
    fake_serial._rx.extend(make_segment(b"ABCDE", is_last=True))

    with pytest.raises(FlukeCommunicationError):
        scope.query_print_png()


def test_save_screen_png_writes_file(scope, fake_serial, tmp_path):
    fake_serial.queue("0")
    fake_serial._rx.extend(b"3,")
    fake_serial._rx.extend(b"0\r")
    fake_serial._rx.extend(make_segment(b"PNG", is_last=True))

    out_file = tmp_path / "screen.png"
    scope.save_screen_png(str(out_file))

    assert out_file.read_bytes() == b"PNG"
