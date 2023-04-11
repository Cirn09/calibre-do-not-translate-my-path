import os
import stat
import shutil


def patch(input: str, new_pyc_file: str, offset: int, output: str | None = None):
    if output is None:
        output = input
    else:
        shutil.copyfile(input, output)
    os.chmod(output, 0o644)
    with open(new_pyc_file, "rb") as f:
        data = f.read()[0x10:]
        
    with open(output, "r+b") as f:
        f.seek(offset)
        f.write(data)
