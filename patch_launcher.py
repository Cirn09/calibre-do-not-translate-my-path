from dataclasses import dataclass
import shutil
import re
import os as _os
import stat
import typing

import click
import lief  # just use lief to parse binary, manually patch

# Config = namedtuple("Config", ("seg_str", "seg_pstr", "seg_index", "sizeof_long"))

Binary = lief.PE.Binary | lief.ELF.Binary | lief.MachO.Binary
Section = lief.PE.Section | lief.ELF.Section | lief.MachO.Section


class IndexNotFoundError(Exception):
    pass


class PstrNotFoundError(Exception):
    pass


class BackendNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class Config(object):
    seg_str: str
    seg_pstr: str
    seg_index: str
    sizeof_long: int


PE_CONFIG = Config(".data", ".data", ".rdata", 4)
ELF_CONFIG = Config(".rodata", ".data.rel.ro", ".rodata", 8)
MACHO_CONFIG = Config("__cstring", "__data", "__const", 8)

WORD_BYTES = 8  # 目前 Calibre 只编译64位，字长统统 8 字节

# PYC_ANCHOR = b"Crypto/Cipher/AES.pyc"
# PYC_BACKEND = b"calibre/db/backend.pyc"
# TODO: 等 https://github.com/lief-project/LIEF/issues/880 完成
PYC_ANCHOR = "Crypto/Cipher/AES.pyc"
PYC_ANCHOR = "Crypto/Cipher/_EKSBlowfish.pyc"
PYC_BACKEND = "calibre/db/backend.pyc"
RE_PYC = re.compile(rb"""[a-zA-Z0-9~!@#$%^&*()_+`\-={}\[\]\|\\:;"'<>,.?/]+\.pyc\0""")


# def p32(x: int) -> bytes:
#     return x.to_bytes(4, "little")


# def p64(x: int) -> bytes:
#     return x.to_bytes(8, "little")


# def ux(x: int, size: int) -> bytes:
#     return x.to_bytes(size, "little")


# def u32(x: bytes):
#     return int.from_bytes(x[:4], "little")


# def u64(x: bytes):
#     return int.from_bytes(x[:8], "little")


# def find_pstr()


class PatchBase(object):
    config: Config
    binary: Binary

    _seg_index: lief.Section | None
    _seg_pstr: lief.Section | None
    _seg_str: lief.Section | None

    display_offset: int

    # offset_index: int
    # offset_pstr: int

    def __init__(self):
        self._seg_index = None
        self._seg_pstr = None
        self._seg_str = None

    @property
    def seg_index(self) -> lief.Section:
        if self._seg_index is None:
            self._seg_index = self.binary.get_section(self.config.seg_index)
        return self._seg_index

    @property
    def seg_pstr(self) -> lief.Section:
        if self._seg_pstr is None:
            self._seg_pstr = self.binary.get_section(self.config.seg_pstr)
        return self._seg_pstr

    @property
    def seg_str(self) -> lief.Section:
        if self._seg_str is None:
            self._seg_str = self.binary.get_section(self.config.seg_str)
        return self._seg_str

    def find_index(self) -> int:
        # [ offset, size ]
        raw = self.seg_index.content
        sizeof_long = self.config.sizeof_long
        for i in range(0, len(raw) - 0x10 * 4, 0x10):  # 对齐
            get_offset_range = lambda j: (
                i + sizeof_long * (j * 2),
                i + sizeof_long * (j * 2 + 1),
            )
            get_size_range = lambda j: (
                i + sizeof_long * (j * 2 + 1),
                i + sizeof_long * (j * 2 + 2),
            )
            if (
                all(raw[j] == 0 for j in range(*get_offset_range(0)))  # 首个 offset 必定为 0
                and any(raw[j] != 0 for j in range(*get_size_range(0)))  # size 必不为 0
                and all(  # 首个文件的 size 必定等于第二个文件的 offset
                    raw[j] == raw[k]
                    for j, k in zip(
                        range(*get_size_range(0)),  # size 0
                        range(*get_offset_range(1)),  # offset 1
                    )
                )
            ):
                # 再检查三个
                prev_offset = int.from_bytes(raw[slice(*get_offset_range(1))], "little")
                prev_size = int.from_bytes(raw[slice(*get_size_range(1))], "little")

                for j in range(3):
                    offset = int.from_bytes(
                        raw[slice(*get_offset_range(2 + j))], "little"
                    )
                    if offset != prev_offset + prev_size:
                        break
                    prev_offset = offset
                    prev_size = int.from_bytes(
                        raw[slice(*get_size_range(2 + j))], "little"
                    )
                else:
                    # self.offset_index = i
                    return i
        raise IndexNotFoundError("PYC item table index not found")

    def find_pstr(self) -> int:
        anchor_offset = self.seg_str.search(PYC_ANCHOR)
        if anchor_offset == 0xFFFFFFFFFFFFFFFF:  # TODO
            raise PstrNotFoundError(f'PYC anchor("{PYC_ANCHOR}") not found')
        # anchor_addr = self.seg_str.offset + anchor_offset + self.binary.imagebase
        anchor_addr = (
            self.binary.imagebase + self.seg_str.virtual_address + anchor_offset
        )
        p = self.seg_pstr.search(anchor_addr, size=WORD_BYTES)
        assert p % WORD_BYTES == 0

        seg_str_start = self.binary.imagebase + self.seg_str.offset
        seg_str_end = seg_str_start + len(self.seg_str.content)

        # 向前找开头，目前 Crypto/Cipher/AES.pyc 对应的位置就是开头，但不排除后续引入了比它更靠前的包
        while p > 0:
            va = int.from_bytes(self.seg_pstr.content[p - WORD_BYTES : p], "little")
            if not seg_str_start <= va < seg_str_end:
                break
            # foa = va - self.binary.imagebase - self.seg_str.virtual_address + self.seg_str.offset
            offset = va - self.binary.imagebase - self.seg_str.virtual_address

            if RE_PYC.match(self.seg_str.content, offset):
                p -= WORD_BYTES
            else:
                break
        # self.offset_pstr = p
        return p

    def find_backend(self) -> tuple[int, int]:
        offset_index = self.find_index()
        offset_pstr_start = self.find_pstr()

        foa_index = self.display_offset + self.seg_index.offset + offset_index
        va_index = self.binary.imagebase + self.seg_index.virtual_address + offset_index
        print(f"PYC item table foa: {foa_index:#x}, va: {va_index:#x}")
        foa_pstr = self.display_offset + self.seg_pstr.offset + offset_pstr_start
        va_pstr = (
            self.binary.imagebase + self.seg_pstr.virtual_address + offset_pstr_start
        )
        print(f"PYC string table foa: {foa_pstr:#x}, va: {va_pstr:#x}")

        offset_str = self.seg_str.search(PYC_BACKEND)
        va = self.binary.imagebase + self.seg_str.virtual_address + offset_str
        offset_pstr = self.seg_pstr.search(va, size=WORD_BYTES)
        index = (offset_pstr - offset_pstr_start) // WORD_BYTES
        offset = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * 2 * index
        )
        size = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * (2 * index + 1)
        )
        print(f"PYC backend offset: {offset:#x}, size: {size:#x}")
        return offset, size


class PatchPE(PatchBase):
    binary: lief.PE.Binary

    def __init__(self, path):
        super().__init__()
        self.binary = lief.PE.parse(path)
        self.config = PE_CONFIG
        self.display_offset = 0


class PatchELF(PatchBase):
    binary: lief.ELF.Binary

    def __init__(self, path):
        super().__init__()
        self.binary = lief.ELF.parse(path)
        self.config = ELF_CONFIG
        self.display_offset = 0


class PatchMachO(PatchBase):
    binary: lief.MachO.Binary
    fat_binary: lief.MachO.FatBinary

    def __init__(self, path):
        super().__init__()
        self.fat_binary = lief.MachO.parse(path)
        self.binary = self.fat_binary.at(0)
        self.config = MACHO_CONFIG
        self.display_offset = self.binary.fat_offset


@click.command()
@click.argument("input", type=click.Path(exists=True), required=True)
@click.argument("output", type=click.Path(exists=False), required=False)
@click.option(
    "os", "-o", "--os", type=click.Choice(["win", "linux", "mac"]), default="win"
)
@click.option("offset", "-f", "--offset", type=click.INT, required=True)
@click.option("size", "-s", "--size", type=click.INT, required=True)
def cli_patch(input: str, output: str, os: str, offset: int, size: int):
    patch(input, output, os, offset, size)


def patch(input: str, output: str | None, os: str, offset: int, size: int):
    if not output:
        output = input
    else:
        shutil.copy(input, output)
    _os.chmod(output, 0o755)
    if os == "win":
        exe = PatchPE(input)
    elif os == "linux":
        exe = PatchELF(input)
    elif os == "mac":
        exe = PatchMachO(input)
    offset_offset, offset_size = exe.find_backend()
    sizeof_long = exe.config.sizeof_long

    with open(output, "rb+") as f:
        f.seek(offset_offset)
        f.write(offset.to_bytes(sizeof_long, "little"))
        f.seek(offset_size)
        f.write(size.to_bytes(sizeof_long, "little"))


if __name__ == "__main__":
    # ppe = PatchPE("./package/calibre-launcher-bk.dll")
    # o, s = ppe.find_backend()
    # print(hex(o), hex(s))

    # pelf = PatchELF("package\\calibre-6.14.1-x86_64\\lib\\libcalibre-launcher.so")
    # o, s = pelf.find_backend()
    # print(hex(o), hex(s))

    # pelf = PatchELF("package\\calibre-6.14.1-arm64\\lib\\libcalibre-launcher.so")
    # o, s = pelf.find_backend()
    # print(hex(o), hex(s))

    # pmo = PatchMachO(
    #     "package\\calibre-6.14.1\\calibre.app\\Contents\\Frameworks\\calibre-launcher.dylib"
    # )
    # o, s = pmo.find_backend()
    # print(hex(o), hex(s))
    cli_patch()
