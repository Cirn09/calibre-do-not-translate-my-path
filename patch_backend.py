# import argparse
import click
import sys
import subprocess
import glob
import os
import shutil

ILLEGAL_WINDOWS = '\\/:*?"<>|'
ILLEGAL_UNIX = "/"
REPLACEMENT_CHAR = "_"
REPLACEMENT_TABLE_WINDOWS = str.maketrans(
    ILLEGAL_WINDOWS, REPLACEMENT_CHAR * len(ILLEGAL_WINDOWS)
)

PATCH_ANCHOR = "# }}}"
PATCH_CODE_WIN = f"""{PATCH_ANCHOR}

{REPLACEMENT_TABLE_WINDOWS = }
def safe_filename(filename):
    return filename.strip().translate(REPLACEMENT_TABLE_WINDOWS)

ascii_filename = safe_filename
"""
PATCH_CODE_UIX = f"""{PATCH_ANCHOR}
def safe_filename(filename):
    return filename.strip().replace({ILLEGAL_UNIX!r}, {REPLACEMENT_CHAR!r})

ascii_filename = safe_filename
"""
ASCII_FILENAME_SUM = 7


# def get_args():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("input", "-i", "--input", help="Input file")
#     parser.add_argument("output", "-o", "--output", help="Output file", required=False)
#     parser.add_argument(
#         "-s", "--os", help="OS to patch for", choices=["win", "nix"], required=True
#     )
#     return parser.parse_args()


@click.command()
@click.argument("input", required=True, type=click.Path(exists=True))
@click.argument("output", required=False, type=click.Path(exists=False))
@click.option(
    "os",
    "-o",
    "--os",
    type=click.Choice(["win", "linux", "mac"]),
    default="win",
)
def cli_patch(input, output, os):
    patch(input, output, os)


def patch(input: str, output: str | None, os: str):

    if output is None:
        output = input

    with open(input, "r") as f:
        old = f.read()

    ascii_filaname_sum = old.count("ascii_filename")
    if ascii_filaname_sum != ASCII_FILENAME_SUM:
        raise Exception(
            f"backend.py ascii_filename count changed ({ascii_filaname_sum}). May cause error! Please check!"
        )

    code = PATCH_ANCHOR
    if os == "win":
        code = PATCH_CODE_WIN
    elif os == "linux" or os == "mac":
        code = PATCH_CODE_UIX

    new = old.replace(PATCH_ANCHOR, code, 1)

    with open(output, "w") as f:
        f.write(new)


def compile(input: str, output: str):
    subprocess.check_output([sys.executable, "-OO", "-m", "py_compile", input])
    name, _ = os.path.splitext(input)
    dir = os.path.join(os.path.dirname(output), "__pycache__")
    pyc = glob.glob(os.path.join(dir, f"{name}.*.pyc"))[0]
    shutil.copy(pyc, output)


if __name__ == "__main__":
    cli_patch()
