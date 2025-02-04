#!/bin/env python3
from glob import glob
import zipfile
import os


def compile_mo():
    for po in glob("translations/*.po"):
        print(f"compiling {po}")
        os.system(
            f'calibre-debug -c "from calibre.translations.msgfmt import main; main()" {po}'
        )


def mkzip():
    filelist = [
        "__init__.py",
        "config.py",
        "plugin-import-name-notrans.txt",
        "ui.py",
        "images/icon.png",
    ]
    for root, dirs, files in os.walk('translations'):
        for f in files:
            if not f.endswith("po"):
                filelist.append(os.path.join(root, f))

    zf = zipfile.ZipFile("NoTrans.zip", "w")
    for file in filelist:
        print(f"compressing {file}")
        zf.write(file)
    zf.close()


if __name__ == "__main__":
    compile_mo()
    mkzip()
