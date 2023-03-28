import click
import zipfile
import os as _os
import typing
from glob import glob

import patch_backend
import patch_launcher
import patch_bypy
import download
import extract


def do_main(
    *,
    version: str,
    os: str,
    package_url: str,
    package_name: str,
    extract_func: typing.Callable[[str, str], None],
    extract_path: str,
    bypy_path: str,
    launcher_path: str,
    zip_path: str,
    zip_launcher_path: str,
    zip_bypy_path: str,
    # python_lib: str,
):

    print(f"[+] downloading Calibre package ...")
    download.download(package_url.format(version=version), package_name)
    print("[+] extracting Calibre installer, it may takes long time ...")
    extract_func(package_name, extract_path)

    # print("[+] checking Calibre python version ...")
    # if not _os.path.exists(python_lib):
    #     dir = _os.path.dirname(python_lib)
    #     maybe_lib = glob(f"{dir}/*python*")
    #     raise Exception(f"Calibre python version changed! usefull info: {maybe_lib}")

    print("[+] patching backend.py ...")
    patch_backend.patch("backend-original.py", "backend.py", os)
    print("[+] compiling backend.py ...")
    patch_backend.compile("backend.py", "backend.pyc")
    new_pyc_size = _os.stat("backend.pyc").st_size - 0x10
    print(f"[+] new pyc size: {new_pyc_size:#x}")

    print("[+] patching bypy ...")
    offset = patch_bypy.patch(
        bypy_path,
        "backend.pyc",
        output=None,
    )

    print("[+] patching calibre-launcher ...")
    patch_launcher.patch(
        launcher_path,
        output=None,
        os=os,
        offset=offset,
        size=new_pyc_size,
    )
    print(f'[+] creating archive "patched-{os}-{version}.zip" ...')

    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(bypy_path, zip_bypy_path)
        z.write(launcher_path, zip_launcher_path)


@click.command()
@click.option(
    "os",
    "-o",
    "--os",
    type=click.Choice(["win", "linux-x64", "linux-arm64", "mac"]),
    default=None,
    required=False,
)
@click.option("version", "-v", "--version", type=click.STRING, required=True)
def cli_main(os: str | None, version: str):
    main(os, version)


def main(os: str | None, version: str):
    print("[+] downloading backend.py ...")
    download.download(
        download.URL_BACKEND.format(version=version), "backend-original.py"
    )

    if os is None or (os is not None and os == "win"):
        print("[+] processing Windows package ...")
        do_main(
            version=version,
            os="win",
            package_url=download.URL_WIN,
            package_name="calibre.msi",
            extract_func=extract.extract_msi,
            extract_path="calibre-win",
            bypy_path="calibre-win/PFiles/Calibre2/app/bin/python-lib.bypy.frozen",
            launcher_path="calibre-win/PFiles/Calibre2/app/bin/calibre-launcher.dll",
            zip_path=f"patch-win-{version}.zip",
            zip_bypy_path="Calibre2/app/bin/python-lib.bypy.frozen",
            zip_launcher_path="Calibre2/app/bin/calibre-launcher.dll",
            # python_lib='calibre-win/PFiles/Calibre2/app/bin/python310.dll'
        )
    if os is None or (os is not None and os == "linux-x64"):
        print("[+] processing Linux x64 package ...")
        do_main(
            version=version,
            os="linux",
            package_url=download.URL_LINUX_x64,
            package_name="calibre-x64.txz",
            extract_func=extract.extract_txz,
            extract_path="calibre-linux-x64",
            bypy_path="calibre-linux-x64/lib/calibre-extensions/python-lib.bypy.frozen",
            launcher_path="calibre-linux-x64/lib/libcalibre-launcher.so",
            zip_path=f"patch-linux-x64-{version}.zip",
            zip_bypy_path="lib/calibre-extensions/python-lib.bypy.frozen",
            zip_launcher_path="lib/libcalibre-launcher.so",
            # python_lib='calibre-linux-x64/lib/libpython3.10.so.1.0'
        )

    if os is None or (os is not None and os == "linux-arm64"):
        print("[+] processing Linux arm64 package ...")
        do_main(
            version=version,
            os="linux",
            package_url=download.URL_LINUX_ARM64,
            package_name="calibre-arm64.txz",
            extract_func=extract.extract_txz,
            extract_path="calibre-linux-arm64",
            bypy_path="calibre-linux-arm64/lib/calibre-extensions/python-lib.bypy.frozen",
            launcher_path="calibre-linux-arm64/lib/libcalibre-launcher.so",
            zip_path=f"patch-linux-arm64-{version}.zip",
            zip_bypy_path="lib/calibre-extensions/python-lib.bypy.frozen",
            zip_launcher_path="lib/libcalibre-launcher.so",
            # python_lib='calibre-linux-arm64/lib/libpython3.10.so.1.0'
        )
    if os is None or (os is not None and os == "mac"):
        print("[+] processing macOS package ...")
        do_main(
            version=version,
            os="mac",
            package_url=download.URL_MAC,
            package_name="calibre.dmg",
            extract_func=extract.extract_dmg,
            extract_path="calibre-mac",
            bypy_path="calibre-mac/calibre.app/Contents/Frameworks/plugins/python-lib.bypy.frozen",
            launcher_path="calibre-mac/calibre.app/Contents/Frameworks/calibre-launcher.dylib",
            zip_path=f"patch-mac-{version}.zip",
            zip_bypy_path="calibre.app/Contents/Frameworks/plugins/python-lib.bypy.frozen",
            zip_launcher_path="calibre.app/Contents/Frameworks/calibre-launcher.dylib",
            # python_lib='calibre-mac/calibre.app/Contents/Frameworks/Python.framework/Versions/3.10/Python'
        )


if __name__ == "__main__":
    # main(os=None, version="6.14.1")
    cli_main()
