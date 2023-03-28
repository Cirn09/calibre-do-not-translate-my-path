import os
import subprocess

# fmt:off
URL_BACKEND = "https://raw.githubusercontent.com/kovidgoyal/calibre/v{version}/src/calibre/db/backend.py"
URL_WIN = "https://download.calibre-ebook.com/{version}/calibre-64bit-{version}.msi"
URL_LINUX_x64 = "https://download.calibre-ebook.com/{version}/calibre-{version}-x86_64.txz"
URL_LINUX_ARM64 = "https://download.calibre-ebook.com/{version}/calibre-{version}-arm64.txz"
URL_MAC = "https://download.calibre-ebook.com/{version}/calibre-{version}.dmg"
# fmt:on


def download(url: str, output: str, overwrite: bool = False):
    if not overwrite and os.path.exists(output):
        return
    subprocess.check_output(["curl", url, "-o", output])


def download_all(version: str):
    download(URL_BACKEND.format(version=version), "backend-original.py")
    download(URL_WIN.format(version=version), "calibre-win.msi")
    download(URL_LINUX_x64.format(version=version), "calibre-linux-x64.txz")
    download(URL_LINUX_ARM64.format(version=version), "calibre-linux-arm64.txz")
    download(URL_MAC.format(version=version), "calibre.dmg")
