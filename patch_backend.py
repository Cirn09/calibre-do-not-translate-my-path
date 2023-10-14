import ast
import sys
import subprocess
import glob
import os
import shutil

import click
import sqlparse

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


def compress_sql(sql: str):
    return sqlparse.format(
        sql, strip_comments=True, strip_whitespace=True
    )  # strip_whitespace 在文档里没写，是Copilot自动补的。检查了源码，还真有这个选项


def compress(input: str, output: str | None):
    if output is None:
        output = input

    with open(input, "r") as f:
        code = f.read()

    _ast = ast.parse(code)

    for node in ast.walk(_ast):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("execute", "executemany")
            and len(node.args) > 0
            and isinstance(node.args[0], ast.Str)
        ):  # 压缩所有 execute*的参数
            sqlcode = node.args[0].value
            sql = compress_sql(sqlcode)
            # node.args[0] = ast.Str(sql)
            node.args[0].value = sql
        elif (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "lines"
        ):
            # 然后是 DB.create_custom_column.lines
            # class DB:
            #     def create_custom_column():
            #         if normalized:
            #             lines = [...]
            #         else:
            #             line = [...]
            for _node in ast.walk(node):
                if isinstance(_node, ast.Str):
                    _node.value = compress_sql(_node.value)

    with open(output, "w") as f:
        f.write(ast.unparse(_ast))


def compile(input: str, output: str):
    subprocess.check_output(["python3.8", "-OO", "-m", "py_compile", input])
    name, _ = os.path.splitext(input)
    dir = os.path.join(os.path.dirname(output), "__pycache__")
    pyc = glob.glob(os.path.join(dir, f"{name}.*.pyc"))[0]
    shutil.copy(pyc, output)


if __name__ == "__main__":
    # cli_patch()
    patch("backend-original.py", "backend-patched.py", "win")
    compress("backend-patched.py", "backend-compressed.py")
    compile("backend-compressed.py", "backend-compressed.pyc")
    compile("backend-original.py", "backend-original.pyc")
    print(os.stat("backend-original.pyc").st_size)
    print(os.stat("backend-compressed.pyc").st_size)
