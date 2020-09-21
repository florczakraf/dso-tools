import argparse
import json
import sys

from dso_tools.dso import DSO


def parse_args(args):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("dso_file", help="Path to dso file")
    options = parser.add_mutually_exclusive_group()
    options.add_argument(
        "--dump-string-table",
        action="store_true",
        help="Dumps global string table to a form that can be later used as a patch",
    )
    options.add_argument(
        "--patch-string-table",
        action="store",
        metavar="PATCH_FILE",
        help="Patches global string table in dso using a patch file",
    )

    return parser.parse_args(args)


def dump_string_table(dso):
    print(json.dumps({i: s.decode() for i, s in enumerate(dso.global_strings)}, indent=4))


def main():
    parsed_args = parse_args(sys.argv[1:])

    with open(parsed_args.dso_file, "rb") as f:
        dso = DSO.from_stream(f)

    if parsed_args.dump_string_table:
        dump_string_table(dso)

    if parsed_args.patch_string_table:
        with open(parsed_args.patch_string_table) as f:
            patch = json.load(f)

        dso.patch_global_strings(patch)

        with open(parsed_args.dso_file, "wb") as f:
            f.write(dso.encode())
