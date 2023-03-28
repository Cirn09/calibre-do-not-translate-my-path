import os
import subprocess


def extract_msi(input: str, output: str):
    subprocess.check_output(["msiextract", input, "-C", output])


def extract_txz(input: str, output: str):
    os.makedirs(output, exist_ok=True)
    subprocess.check_output(["tar", "Jxf", input, "-C", output])


def extract_dmg(input: str, output: str):
    subprocess.run(
        ["7zz", "x", "-y", input, "-o" + output], check=False, stdout=subprocess.PIPE
    )
