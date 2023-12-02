import subprocess
import sys
import os
import glob
import shutil

import click


def compile(input: str, output: str):
    subprocess.check_output([sys.executable, "-OO", "-m", "py_compile", input])
    name, _ = os.path.splitext(input)
    dir = os.path.join(os.path.dirname(output), "__pycache__")
    pyc = glob.glob(os.path.join(dir, f"{name}.*.pyc"))[0]
    shutil.copy(pyc, output)


@click.command()
@click.argument("input", required=True, type=click.Path(exists=True))
@click.argument("output", required=False, type=click.Path(exists=False))
def cli_compile(input: str, output: str):
    compile(input, output)


if __name__ == "__main__":
    cli_compile()
