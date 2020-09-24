import json
import subprocess

import pytest

from dso_tools.dso import DSO, normalize_code
from dso_tools.main import parse_args


def test_dump_string_table(tmp_path):
    dso = DSO()
    dso.global_strings = [b"", b"second", b"third", b""]
    dso_file = tmp_path / "dso_file"
    dso_file.write_bytes(dso.encode())

    result = subprocess.check_output(["dso", "--dump-string-table", dso_file.as_posix()], text=True)

    assert (
        result
        == """\
{
    "0": "",
    "1": "second",
    "2": "third",
    "3": ""
}
"""
    )


def test_argument_parser():
    with pytest.raises(SystemExit):
        parse_args([])

    parsed = parse_args(["/path/to/dso"])
    assert parsed.dso_file == "/path/to/dso"

    parsed = parse_args(["--dump-string-table", "/path/to/dso"])
    assert parsed.dso_file == "/path/to/dso"
    assert parsed.dump_string_table is True

    parsed = parse_args(["--patch-string-table", "/path/to/patch/file", "/path/to/dso"])
    assert parsed.dso_file == "/path/to/dso"
    assert parsed.patch_string_table == "/path/to/patch/file"

    with pytest.raises(SystemExit):
        parse_args(["--dump-string-table", "--patch-string-table", "/path/to/patch/file", "/path/to/dso"])


def test_patch_string_table(tmp_path):
    dso = DSO()
    dso.global_strings = [b"", b"second", b"third", b""]
    dso.code = [
        b"\x54",  # OP_ASSERT
        b"\x08",  # offset for "third"
        b"\x46",  # OP_LOADIMMED_STR
        b"\x01",  # offset for "second"
        b"\x00",  # to be patched in runtime
    ]
    dso.string_references = [(8, [4])]
    dso_file = tmp_path / "dso_file"
    dso_file.write_bytes(dso.encode())

    patch = {1: "foo"}
    patch_file = tmp_path / "patch_file"
    patch_file.write_text(json.dumps(patch))

    subprocess.check_call(["dso", "--patch-string-table", patch_file.as_posix(), dso_file.as_posix()])

    with dso_file.open("rb") as stream:
        new_dso = DSO.from_stream(stream)

    assert new_dso.global_strings == [b"", b"foo", b"third", b""]
    assert normalize_code(new_dso.code) == normalize_code(
        [
            b"\x54",  # OP_ASSERT
            b"\x05",  # new offset for "third"
            b"\x46",  # OP_LOADIMMED_STR
            b"\x01",  # offset for "foo"
            b"\x00",  # to be patched in runtime
        ]
    )
    assert new_dso.string_references == [(5, [4])]
