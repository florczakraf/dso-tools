import struct

from dso_tools.opcodes import OPCODES

SUPPORTED_DSO_VERSIONS = (43,)
U32_BYTES = 4
FLOAT_BYTES = 8


class DSO:
    version = SUPPORTED_DSO_VERSIONS[0]
    global_strings = []
    function_strings = []
    global_floats = []
    function_floats = []
    code = []
    line_break_count = 0
    string_references = []

    @staticmethod
    def from_stream(stream):
        dso = DSO()

        dso.protocol_version = parse_protocol_version(stream)
        dso.global_strings = parse_string_table(stream)
        dso.function_strings = parse_string_table(stream)
        dso.global_floats = parse_float_table(stream)
        dso.function_floats = parse_float_table(stream)
        dso.code, dso.line_break_count = parse_code(stream)
        dso.string_references = parse_string_references(stream)

        return dso

    def encode(self):
        buffer = eu32(self.version)
        buffer += encode_string_table(self.global_strings)
        buffer += encode_string_table(self.function_strings)
        buffer += encode_float_table(self.global_floats)
        buffer += encode_float_table(self.function_floats)
        buffer += encode_code(self.code, self.line_break_count)
        buffer += encode_string_references(self.string_references)

        return buffer

    def patch_global_strings(self, patches):
        new_global_strings = self.global_strings.copy()
        new_code = self.code.copy()
        new_string_references = []

        for i, new_value in patches.items():
            new_global_strings[int(i)] = new_value.encode()

        for ip, instruction in enumerate(self.code):
            if is_opcode(instruction):
                op = OPCODES[u8(instruction)]
                if op in ("OP_TAG_TO_STR", "OP_LOADIMMED_STR", "OP_DOCBLOCK_STR", "OP_ASSERT"):
                    offset = bytes_to_int(new_code[ip + 1])
                    new_offset = get_new_string_offset(offset, self.global_strings, new_global_strings)

                    new_code[ip + 1] = eu32(new_offset)

        for offset, occurrences in self.string_references:
            new_offset = get_new_string_offset(offset, self.global_strings, new_global_strings)
            new_string_references.append((new_offset, occurrences))

        self.global_strings = new_global_strings
        self.code = new_code
        self.string_references = new_string_references


def encode_string_references(string_references):
    buffer = eu32(len(string_references))
    for offset, occurrences in string_references:
        buffer += eu32(offset)
        buffer += eu32(len(occurrences))
        for occurrence in occurrences:
            buffer += eu32(occurrence)

    return buffer


def parse_string_references(stream):
    string_references_count = u32(stream)
    string_references = []
    for _ in range(string_references_count):
        offset = u32(stream)
        occurrences_count = u32(stream)
        occurrences = []
        for _ in range(occurrences_count):
            occurrences.append(u32(stream))
        string_references.append((offset, occurrences))

    return string_references


def parse_code(stream):
    instruction_count = u32(stream)
    line_break_pair_count = u32(stream)
    line_break_count = 2 * line_break_pair_count

    code = []
    for i in range(instruction_count):
        peek = stream.read(1)
        if peek == b"\xff":
            code.append(stream.read(U32_BYTES))
        else:
            code.append(peek)

    for i in range(line_break_count):
        code.append(stream.read(U32_BYTES))

    return code, line_break_count


def parse_float_table(stream):
    floats_count = u32(stream)
    format_string = "<" + "d" * floats_count
    return list(struct.unpack(format_string, stream.read(floats_count * FLOAT_BYTES)))


def encode_float_table(float_table):
    format_string = "<" + "d" * len(float_table)
    return eu32(len(float_table)) + struct.pack(format_string, *float_table)


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


def encode_code(code, line_break_count):
    buff = b""
    for instruction in code[0 : len(code) - line_break_count]:
        if len(instruction) == 4:
            buff += b"\xff"

        buff += instruction

    for instruction in code[len(code) - line_break_count :]:
        buff += instruction

    return eu32(len(code) - line_break_count) + eu32(line_break_count // 2) + buff


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


def parse_protocol_version(stream):
    version = u32(stream)
    if version not in SUPPORTED_DSO_VERSIONS:
        raise ValueError(f"dso version {version} is not on supported list ({SUPPORTED_DSO_VERSIONS})")

    return version


def parse_string_table(stream):
    strings_length = u32(stream)
    string_table = stream.read(strings_length).split(b"\x00")

    return string_table


def normalize_code(code):
    r"""
    Every single byte (\xXX) instruction in code can be also represented by the equivalent,
    yet more verbose form of \xXX\x00\x00\x00, which is later represented by \xff\xXX\x00\x00\x00 in encoded form.
    """
    return [eu32(bytes_to_int(instruction)) for instruction in code]
