import pytest
from dso_tools.dso import DSO
from dso_tools.main import dump_string_table, parse_args


def test_dump_string_table(capsys):
    dso = DSO()
    dso.global_strings = [b"", b"second", b"third", b""]

    dump_string_table(dso)

    captured = capsys.readouterr().out
    assert (
        captured
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
