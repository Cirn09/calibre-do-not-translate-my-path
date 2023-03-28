import os
import stat
import shutil


def patch(input: str, new_pyc_file: str, output: str | None = None) -> int:
    if output is None:
        output = input
    else:
        shutil.copyfile(input, output)
    os.chmod(output, stat.S_IWRITE)
    with open(new_pyc_file, "rb") as f:
        data = f.read()[0x10:]
    with open(output, "ab") as f:
        size = f.tell()
        f.write(data)

    return size
