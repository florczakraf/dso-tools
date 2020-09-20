import io

import pytest
from dso_tools.dso import (
    offset_to_string_index,
    string_index_to_offset,
    get_new_string_offset,
    encode_string_table,
    bytes_to_int,
    is_opcode,
    encode_code,
    offset_to_string,
    u32,
    eu32,
    parse_protocol_version,
    parse_string_table,
    get_raw_string_table,
    parse_float_table,
    encode_float_table,
    parse_code,
    parse_string_references,
    encode_string_references,
)


def test_get_raw_string_table():
    assert get_raw_string_table([]) == b""
    assert get_raw_string_table([b""]) == b""
    assert get_raw_string_table([b"", b"second", b"third", b""]) == b"\x00second\x00third\x00"


def test_encode_string_table():
    assert encode_string_table([]) == b"\x00\x00\x00\x00"
    assert encode_string_table([b""]) == b"\x00\x00\x00\x00"
    assert encode_string_table([b"", b"second", b"third", b""]) == b"\x0e\x00\x00\x00\x00second\x00third\x00"


def test_offset_to_string_index():
    string_table = [b"", b"second", b"third", b""]

    assert offset_to_string_index(0, string_table) == 0
    assert offset_to_string_index(1, string_table) == 1
    assert offset_to_string_index(8, string_table) == 2
    assert offset_to_string_index(13, string_table) == 3


def test_string_index_to_offset():
    string_table = [b"", b"second", b"third", b""]

    assert string_index_to_offset(0, string_table) == 0
    assert string_index_to_offset(1, string_table) == 1
    assert string_index_to_offset(2, string_table) == 8
    assert string_index_to_offset(3, string_table) == 13


def test_get_new_string_offset():
    string_table = [b"", b"second", b"third", b""]
    new_string_table = [b"", b"longer string", b"third", b""]

    assert get_new_string_offset(0, string_table, new_string_table) == 0
    assert get_new_string_offset(1, string_table, new_string_table) == 1
    assert get_new_string_offset(8, string_table, new_string_table) == 15
    assert get_new_string_offset(13, string_table, new_string_table) == 20


def test_bytes_to_int():
    assert bytes_to_int(b"\x0a") == 10
    assert bytes_to_int(b"\x09\x00\x00\x00") == 9
    assert bytes_to_int(b"\x01\x01\x00\x00") == 257

    with pytest.raises(ValueError):
        bytes_to_int(b"\x00\x00\x00\x00\x00")
    with pytest.raises(ValueError):
        bytes_to_int(b"\x00\x00")
    with pytest.raises(ValueError):
        bytes_to_int(b"")


def test_u32_from_stream():
    stream = io.BytesIO(b"\x2a\x00\x00\x00\xff\xff\x00\x00\xab\xcd")

    assert u32(stream) == 42
    assert u32(stream) == 65535
    assert stream.read() == b"\xab\xcd"
    with pytest.raises(ValueError):
        u32(stream)


def test_u32_from_bytes():
    assert u32(b"\x2a\x00\x00\x00") == 42
    assert u32(b"\x00\x01\x00\x00") == 256

    with pytest.raises(ValueError):
        u32(b"")
    with pytest.raises(ValueError):
        u32(b"\x00")


def test_is_opcode():
    assert is_opcode(b"\x00") is True
    assert is_opcode(b"\x42") is True
    assert is_opcode(b"\x5a") is True
    assert is_opcode(b"\x5b") is False
    assert is_opcode(b"\x00\x00") is False
    assert is_opcode(b"\x42\x00") is False


def test_encode_code():
    code = [b"\x00", b"\x00\x00\x00\x00", b"\x01", b"\x02", b"\x03", b"\x01\x02\x03\x04", b"\x05\x06\x07\x08"]
    line_break_count = 2

    assert encode_code(code, line_break_count) == (
        b"\x05\x00\x00\x00"
        b"\x01\x00\x00\x00"
        b"\x00"
        b"\xff\x00\x00\x00\x00"
        b"\x01"
        b"\x02"
        b"\x03"
        b"\x01\x02\x03\x04"
        b"\x05\x06\x07\x08"
    )


def test_offset_to_string():
    string_table = [b"", b"second", b"third", b""]

    assert offset_to_string(0, string_table) == b""
    assert offset_to_string(1, string_table) == b"second"
    assert offset_to_string(8, string_table) == b"third"
    assert offset_to_string(13, string_table) == b""


def test_eu32():
    assert eu32(0) == b"\x00\x00\x00\x00"
    assert eu32(5) == b"\x05\x00\x00\x00"
    assert eu32(42) == b"\x2a\x00\x00\x00"
    assert eu32(257) == b"\x01\x01\x00\x00"

    with pytest.raises(ValueError) as e:
        eu32(int(1e10))


def test_parse_protocol_version():
    stream = io.BytesIO(b"\x2b\x00\x00\x00\xab\xcd")

    assert parse_protocol_version(stream) == 43
    assert stream.read() == b"\xab\xcd"

    stream = io.BytesIO(b"\x2c\x00\x00\x00")

    with pytest.raises(ValueError):
        parse_protocol_version(stream)


def test_parse_empty_string_table():
    stream = io.BytesIO(b"\x00\x00\x00\x00\xab\xcd")

    assert parse_string_table(stream) == [b""]
    assert stream.read() == b"\xab\xcd"


def test_parse_string_table():
    stream = io.BytesIO(b"\x0e\x00\x00\x00\x00second\x00third\x00\xab\xcd")

    assert parse_string_table(stream) == [b"", b"second", b"third", b""]
    assert stream.read() == b"\xab\xcd"


def test_parse_empty_float_table():
    stream = io.BytesIO(b"\x00\x00\x00\x00\xab\xcd")
    assert parse_float_table(stream) == []
    assert stream.read() == b"\xab\xcd"


def test_parse_float_table():
    stream = io.BytesIO(
        b"\x02\x00\x00\x00" b"\x00\x00\x00\x00\x00\x00\xf8\x3f" b"\xcd\xcc\xcc\xcc\xcc\x0c\x45\x40" b"\xab\xcd"
    )
    assert parse_float_table(stream) == [1.5, 42.1]
    assert stream.read() == b"\xab\xcd"


def test_encode_float_table():
    assert encode_float_table([]) == b"\x00\x00\x00\x00"
    assert encode_float_table([1.5, 42.1]) == (
        b"\x02\x00\x00\x00" b"\x00\x00\x00\x00\x00\x00\xf8\x3f" b"\xcd\xcc\xcc\xcc\xcc\x0c\x45\x40"
    )


def test_parse_empty_code():
    stream = io.BytesIO(b"\x00\x00\x00\x00" b"\x00\x00\x00\x00" b"\xab\xcd")

    assert parse_code(stream) == ([], 0)
    assert stream.read() == b"\xab\xcd"


def test_parse_code():
    stream = io.BytesIO(
        b"\x02\x00\x00\x00"
        b"\x01\x00\x00\x00"
        b"\xff\x01\x00\x00\x00"
        b"\x4a"
        b"\x01\x23\x45\x67"
        b"\x89\xab\xcd\xef"
        b"\xab\xcd"
    )

    assert parse_code(stream) == ([b"\x01\x00\x00\x00", b"\x4a", b"\x01\x23\x45\x67", b"\x89\xab\xcd\xef"], 2)
    assert stream.read() == b"\xab\xcd"


def test_parse_empty_string_references():
    stream = io.BytesIO(eu32(0) + b"\xab\xcd")

    assert parse_string_references(stream) == []
    assert stream.read() == b"\xab\xcd"


def test_parse_string_references():
    stream = io.BytesIO(eu32(2) + eu32(0) + eu32(2) + eu32(4) + eu32(42) + eu32(32) + eu32(1) + eu32(7) + b"\xab\xcd")

    assert parse_string_references(stream) == [
        (0, [4, 42]),
        (32, [7]),
    ]
    assert stream.read() == b"\xab\xcd"


def test_encode_empty_string_references():
    assert encode_string_references([]) == eu32(0)


def test_encode_string_references():
    string_references = [(0, [4, 42]), (32, [7])]
    expected = eu32(2) + eu32(0) + eu32(2) + eu32(4) + eu32(42) + eu32(32) + eu32(1) + eu32(7)

    assert encode_string_references(string_references) == expected
