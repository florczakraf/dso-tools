import io

import pytest
from dso_tools.dso import (
    make_string_table,
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
)


def test_make_string_table():
    raw_strings = b"\x00second\x00third\x00"

    result = make_string_table(raw_strings)

    assert result == [b"", b"second", b"third", b""]
    assert b"\x00".join(result) == raw_strings


def test_encode_string_table():
    assert encode_string_table([b"", b"second", b"third", b""]) == b"\x00second\x00third\x00"


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
    stream = io.BytesIO(b"\x2a\x00\x00\x00\xff\xff\x00\x00")

    assert u32(stream) == 42
    assert u32(stream) == 65535
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
    code = [b"\x00", b"\x00\x00\x00\x00", b"\x01", b"\x02", b"\x03", b"\x01\x02\x03\x04"]

    assert encode_code(code) == b"\x00\xff\x00\x00\x00\x00\x01\x02\x03\xff\x01\x02\x03\x04"


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
