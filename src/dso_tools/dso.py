import struct

from dso_tools.opcodes import OPCODES

U32_BYTES = 4


def is_opcode(instruction):
    return len(instruction) == 1 and u8(instruction) < len(OPCODES)


def get_new_string_offset(offset, string_table, new_string_table):
    string_index = offset_to_string_index(offset, string_table)
    new_offset = string_index_to_offset(string_index, new_string_table)

    return new_offset


def get_raw_string_table(string_table):
    return b"\x00".join(string_table)


def encode_string_table(string_table):
    raw_strings = get_raw_string_table(string_table)
    return eu32(len(raw_strings)) + raw_strings


def encode_code(code):
    buff = b""
    for instruction in code:
        if len(instruction) == 4:
            buff += b"\xff"

        buff += instruction

    return buff


def eu32(v):
    try:
        return struct.pack("<I", v)
    except Exception as e:
        raise ValueError(f"can't encode {v} as u32") from e


def bytes_to_int(one_or_four_bytes):
    if len(one_or_four_bytes) not in (1, 4):
        raise ValueError("provide one or four bytes")

    if len(one_or_four_bytes) == 1:
        return u8(one_or_four_bytes)

    return u32(one_or_four_bytes)


def string_index_to_offset(index, string_table):
    if index == len(string_table) - 1:
        return len(b"\x00".join(string_table)) - 1

    return len(b"\x00".join(string_table[: index + 1])) - len(string_table[index])


def offset_to_string_index(offset, string_table):
    raw_strings = get_raw_string_table(string_table)

    if offset == len(raw_strings) - 1:
        return len(raw_strings.split(b"\x00")) - 1
    return raw_strings[:offset].count(b"\x00")


def u8(byte):
    return struct.unpack("<B", byte)[0]


def u32(four_bytes_or_stream):
    if not isinstance(four_bytes_or_stream, bytes):
        four_bytes_or_stream = four_bytes_or_stream.read(U32_BYTES)

    if len(four_bytes_or_stream) != 4:
        raise ValueError("provide four bytes")

    return struct.unpack("<I", four_bytes_or_stream)[0]


def offset_to_string(offset, string_table):
    raw_string = get_raw_string_table(string_table)
    end = raw_string.index(b"\00", offset)

    return raw_string[offset:end]


def parse_string_table(stream):
    strings_length = u32(stream)
    string_table = stream.read(strings_length).split(b"\x00")

    return string_table
