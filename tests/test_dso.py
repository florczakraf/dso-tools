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
    DSO,
    normalize_code,
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

    with pytest.raises(ValueError, match="^provide one or four bytes$"):
        bytes_to_int(b"\x00\x00\x00\x00\x00")
    with pytest.raises(ValueError, match="^provide one or four bytes$"):
        bytes_to_int(b"\x00\x00")
    with pytest.raises(ValueError, match="^provide one or four bytes$"):
        bytes_to_int(b"")


def test_u32_from_stream():
    stream = io.BytesIO(b"\x2a\x00\x00\x00\xff\xff\x00\x00\xab\xcd")

    assert u32(stream) == 42
    assert u32(stream) == 65535
    assert stream.read() == b"\xab\xcd"
    with pytest.raises(ValueError, match="^provide four bytes$"):
        u32(stream)


def test_u32_from_bytes():
    assert u32(b"\x2a\x00\x00\x00") == 42
    assert u32(b"\x00\x01\x00\x00") == 256

    with pytest.raises(ValueError, match="provide four bytes"):
        u32(b"")
    with pytest.raises(ValueError, match="provide four bytes"):
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


def test_encode_code_without_line_breaks():
    code = [b"\x00", b"\x2a\x2a\x00\x00", b"\x01"]
    line_break_count = 0

    assert encode_code(code, line_break_count) == (
        b"\x03\x00\x00\x00" b"\x00\x00\x00\x00" b"\x00" b"\xff\x2a\x2a\x00\x00" b"\x01"
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


def test_create_dso_from_stream():
    stream = io.BytesIO(
        b"\x2b\x00\x00\x00"  # protocol version
        b"\x0e\x00\x00\x00\x00second\x00third\x00"  # global string table
        b"\x05\x00\x00\x00\x00foo\x00"  # function string table
        b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf8\x3f"  # global float table
        b"\x01\x00\x00\x00\xcd\xcc\xcc\xcc\xcc\x0c\x45\x40"  # string float table
        b"\x02\x00\x00\x00\x01\x00\x00\x00\xff\x01\x00\x00\x00\x4a\x01\x23\x45\x67\x89\xab\xcd\xef"  # code
        b"\x01\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00"  # string references
        b"\xab\xcd"
    )

    dso = DSO.from_stream(stream)

    assert dso.version == 43
    assert dso.global_strings == [b"", b"second", b"third", b""]
    assert dso.function_strings == [b"", b"foo", b""]
    assert dso.global_floats == [1.5]
    assert dso.function_floats == [42.1]
    assert dso.code == [b"\x01\x00\x00\x00", b"\x4a", b"\x01\x23\x45\x67", b"\x89\xab\xcd\xef"]
    assert dso.line_break_count == 2
    assert dso.string_references == [(1, [3, 4])]
    assert stream.read() == b"\xab\xcd"


def test_encode_dso():
    dso = DSO()
    dso.version = 43
    dso.global_strings = [b"", b"second", b"third", b""]
    dso.function_strings = [b"", b"foo", b""]
    dso.global_floats = [1.5]
    dso.function_floats = [42.1]
    dso.code = [b"\x01\x00\x00\x00", b"\x4a", b"\x01\x23\x45\x67", b"\x89\xab\xcd\xef"]
    dso.line_break_count = 2
    dso.string_references = [(1, [3, 4])]

    assert dso.encode() == (
        b"\x2b\x00\x00\x00"  # protocol version
        b"\x0e\x00\x00\x00\x00second\x00third\x00"  # global string table
        b"\x05\x00\x00\x00\x00foo\x00"  # function string table
        b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf8\x3f"  # global float table
        b"\x01\x00\x00\x00\xcd\xcc\xcc\xcc\xcc\x0c\x45\x40"  # string float table
        b"\x02\x00\x00\x00\x01\x00\x00\x00\xff\x01\x00\x00\x00\x4a\x01\x23\x45\x67\x89\xab\xcd\xef"  # code
        b"\x01\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00"  # string references
    )


def test_normalize_code():
    assert normalize_code([]) == []
    assert normalize_code([b"\x2a"]) == [b"\x2a\x00\x00\x00"]
    assert normalize_code([b"\x2a\x00\x00\x00"]) == [b"\x2a\x00\x00\x00"]
    assert normalize_code([b"\x2a\x00\x00\x00", b"\x01"]) == [b"\x2a\x00\x00\x00", b"\x01\x00\x00\x00"]


def test_patch_global_strings():
    dso = DSO()
    dso.version = 43
    dso.global_strings = [b"", b"second", b"third", b"fourth", b""]
    dso.code = [
        b"\x01",  # some not interesting opcode
        b"\x08",  # arbitrary value that's also an offset for "third"
        b"\x45",  # OP_TAG_TO_STR
        b"\x08",  # offset for "third"
        b"\x46",  # OP_LOADIMMED_STR
        b"\x08",  # offset for "third"
        b"\x47",  # OP_DOCBLOCK_STR
        b"\x08",  # offset for "third"
        b"\x54",  # OP_ASSERT
        b"\x08",  # offset for "third"
        b"\x46",  # OP_LOADIMMED_STR
        b"\x01",  # offset for "second"
        b"\x46",  # OP_LOADIMMED_STR
        b"\x0e",  # offset for "fourth"
        b"\x02",  # another not interesting opcode
        b"\x00",  # this will be patched using string_references
        b"\x00",  # this will be patched using string_references
    ]
    dso.string_references = [(1, [13]), (8, [14])]

    dso.patch_global_strings({1: "s e c o n d", "2": "third"})

    assert dso.global_strings == [b"", b"s e c o n d", b"third", b"fourth", b""]
    assert normalize_code(dso.code) == normalize_code(
        [
            b"\x01",  # some not interesting opcode
            b"\x08",  # unchanged value
            b"\x45",  # OP_TAG_TO_STR
            b"\x0d",  # offset for "third"
            b"\x46",  # OP_LOADIMMED_STR
            b"\x0d",  # offset for "third"
            b"\x47",  # OP_DOCBLOCK_STR
            b"\x0d",  # offset for "third"
            b"\x54",  # OP_ASSERT
            b"\x0d",  # offset for "third"
            b"\x46",  # OP_LOADIMMED_STR
            b"\x01",  # offset for "s e c o n d"
            b"\x46",  # OP_LOADIMMED_STR
            b"\x13",  # offset for "fourth"
            b"\x02",  # another not interesting opcode
            b"\x00",  # this will be patched using string_references
            b"\x00",  # this will be patched using string_references
        ]
    )
    assert dso.string_references == [(1, [13]), (13, [14])]
