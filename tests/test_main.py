import subprocess

import pytest

from dso_tools.dso import DSO
from dso_tools.main import parse_args


def test_dump_string_table(capsys, tmp_path):
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
