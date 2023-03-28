import os
import subprocess


def extract_msi(input: str, output: str, overwrite: bool = False):
    if not overwrite and os.path.exists(output):
        return
    subprocess.check_output(["msiextract", input, "-C", output])


def extract_txz(input: str, output: str, overwrite: bool = False):
    if not overwrite and os.path.exists(output):
        return
    os.makedirs(output, exist_ok=True)
    subprocess.check_output(["tar", "Jxf", input, "-C", output])


def extract_dmg(input: str, output: str, overwrite: bool = False):
    if not overwrite and os.path.exists(output):
        return
    subprocess.run(
        [
            "7zz",
            "x",
            "-y",
            "-o" + output,
            input,
            "calibre.app/Contents/Frameworks/plugins/python-lib.bypy.frozen",
            "calibre.app/Contents/Frameworks/calibre-launcher.dylib",
        ],
        check=False,
        stdout=subprocess.PIPE,
    )
