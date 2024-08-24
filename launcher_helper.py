from dataclasses import dataclass
import shutil
import re
import os as _os
import stat
import typing
import traceback

import click
import lief

# Config = namedtuple("Config", ("seg_str", "seg_pstr", "seg_index", "sizeof_long"))

Binary = lief.PE.Binary | lief.ELF.Binary | lief.MachO.Binary
Section = lief.PE.Section | lief.ELF.Section | lief.MachO.Section


class IndexNotFoundError(Exception):
    pass


class DataNotFoundError(Exception):
    pass


class SectionNotFoundError(Exception):
    pass


class BackendNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class Config(object):
    seg_str: str
    seg_pstr: str
    seg_pstr_os: str
    seg_index: str
    sizeof_long: int


PE_CONFIG = Config(
    seg_str=".data",
    seg_pstr=".data",
    seg_pstr_os="UNK",
    seg_index=".rdata",
    sizeof_long=4,
)
ELF_CONFIG = Config(
    seg_str=".rodata",
    seg_pstr=".data.rel.ro",
    seg_pstr_os="UNK",
    seg_index=".rodata",
    sizeof_long=8,
)
MACHO_CONFIG = Config(
    seg_str="__cstring",
    seg_pstr="__data",
    seg_pstr_os="__const",
    seg_index="__const",
    sizeof_long=8,
)

WORD_BYTES = 8  # 目前 Calibre 只编译64位，字长统统 8 字节
OS_ELEMENY_SIZE = 4
NO_OS_ELEMENY_SIZE = 8

PYC_ANCHOR = b"Crypto/Cipher/AES.pyc"
RE_PYC = re.compile(rb"""[a-zA-Z0-9~!@#$%^&*()_+`\-={}\[\]\|\\:;"'<>,.?/]+\.pyc\0""")


def get_anchor_str(buf: memoryview) -> bytes:
    match = RE_PYC.search(buf)
    if match is None:
        raise DataNotFoundError()
    return match.group()


class HelperBase(object):
    config: Config
    binary: Binary

    _seg_index: lief.Section | None
    _seg_pstr: lief.Section | None
    _seg_pstr_os: lief.Section | None
    _seg_str: lief.Section | None

    display_offset: int

    # offset_index: int
    # offset_pstr: int

    def __init__(self):
        self._seg_index = None
        self._seg_pstr = None
        self._seg_pstr_os = None
        self._seg_str = None

    @property
    def seg_index(self) -> lief.Section:
        if self._seg_index is None:
            self._seg_index = self.binary.get_section(self.config.seg_index)
            if self._seg_index is None:
                raise SectionNotFoundError(
                    f"section {self.config.seg_index} not found!"
                )
        return self._seg_index

    @property
    def seg_pstr(self) -> lief.Section:
        if self._seg_pstr is None:
            self._seg_pstr = self.binary.get_section(self.config.seg_pstr)
            if self._seg_pstr is None:
                raise SectionNotFoundError(f"section {self.config.seg_pstr} not found!")
        return self._seg_pstr

    @property
    def seg_pstr_os(self) -> lief.Section:
        if self._seg_pstr_os is None:
            self._seg_pstr_os = self.binary.get_section(self.config.seg_pstr_os)
            if self._seg_pstr_os is None:
                raise SectionNotFoundError(
                    f"section {self.config.seg_pstr_os} not found!"
                )
        return self._seg_pstr_os

    @property
    def seg_str(self) -> lief.Section:
        if self._seg_str is None:
            self._seg_str = self.binary.get_section(self.config.seg_str)
            if self._seg_str is None:
                raise SectionNotFoundError(f"section {self.config.seg_str} not found!")
        return self._seg_str

    def find_index(self) -> int:
        # [ offset, size ]
        raw = self.seg_index.content
        sizeof_long = self.config.sizeof_long
        for i in range(0, len(raw) - 0x10 * 4, sizeof_long):  # 对齐
            get_offset_range = lambda j: (
                i + sizeof_long * (j * 2),
                i + sizeof_long * (j * 2 + 1),
            )
            get_size_range = lambda j: (
                i + sizeof_long * (j * 2 + 1),
                i + sizeof_long * (j * 2 + 2),
            )
            if (
                all(
                    raw[j] == 0 for j in range(*get_offset_range(0))
                )  # 首个 offset 必定为 0
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

    def find_pstr_os(self) -> int:
        """finding string pointer array in -Os binary"""
        try:
            anchor = get_anchor_str(self.seg_str.content)
        except DataNotFoundError:
            raise DataNotFoundError(f"anchor not found in seg {self.config.seg_str}")

        anchor_offset = self.seg_str.search(anchor)
        if anchor_offset is None:
            raise DataNotFoundError(f'PYC anchor("{PYC_ANCHOR}") not found')
        anchor_addr = (
            self.binary.imagebase + self.seg_str.virtual_address + anchor_offset
        )

        p = None
        seg_base = self.binary.imagebase + self.seg_pstr_os.virtual_address
        for i in range(0, len(self.seg_pstr_os.content), OS_ELEMENY_SIZE):
            addr = seg_base + i
            buf = self.seg_pstr_os.content[i : i + OS_ELEMENY_SIZE]
            content = int.from_bytes(buf, "little")
            target = (addr + content) & 0xFFFFFFFF
            if target == anchor_addr:
                p = i
                break

        if p is None:
            raise DataNotFoundError(f'data pointer to anchor("{PYC_ANCHOR}") not found')
        if p % OS_ELEMENY_SIZE != 0:
            raise ValueError("search result not algined!")

        return p

    def find_pstr_no_os(self) -> int:
        """finding string pointer array in non -Os binary"""
        try:
            anchor = get_anchor_str(self.seg_str.content)
        except DataNotFoundError:
            raise DataNotFoundError(f"anchor not found in seg {self.config.seg_str}")

        anchor_offset = self.seg_str.search(anchor)
        if anchor_offset is None:
            raise DataNotFoundError(f'PYC anchor("{PYC_ANCHOR}") not found')
        anchor_addr = (
            self.binary.imagebase + self.seg_str.virtual_address + anchor_offset
        )

        p = self.seg_pstr.search(anchor_addr, size=NO_OS_ELEMENY_SIZE)
        if p is None:
            # 不知道为什么，macOS elf 部分数据指针有 0x00100000 00000000 偏移，部分指针又没有偏移，ida 能纠正这个偏移
            # 搜了一下没找着是什么技术
            # 只搜索 4 字节能消除这个偏移的影响
            p = self.seg_pstr.search(anchor_addr, size=4)
            if p is None:
                raise DataNotFoundError(
                    f'data pointer to anchor("{PYC_ANCHOR}") not found'
                )
        if p % NO_OS_ELEMENY_SIZE != 0:
            raise ValueError("search result not algined!")

        return p

    def find_target_no_os(self, target) -> tuple[int, int]:
        offset_index = self.find_index()
        offset_pstr_start = self.find_pstr_no_os()

        foa_index = self.display_offset + self.seg_index.offset + offset_index
        va_index = self.binary.imagebase + self.seg_index.virtual_address + offset_index
        print(f"[+] PYC item table foa: {foa_index:#x}, va: {va_index:#x}")
        foa_pstr = self.display_offset + self.seg_pstr.offset + offset_pstr_start
        va_pstr = (
            self.binary.imagebase + self.seg_pstr.virtual_address + offset_pstr_start
        )
        print(f"[+] PYC string table foa: {foa_pstr:#x}, va: {va_pstr:#x}")

        offset_str = self.seg_str.search(target)
        if offset_str is None:
            raise DataNotFoundError(f'target "{target}" not found')
        va = self.binary.imagebase + self.seg_str.virtual_address + offset_str
        offset_pstr = self.seg_pstr.search(va, size=NO_OS_ELEMENY_SIZE)
        if offset_pstr is None:
            offset_pstr = self.seg_pstr.search(va, size=4)
            if offset_pstr is None:
                raise DataNotFoundError(f'pointer to target "{target}" not found')
        index = (offset_pstr - offset_pstr_start) // NO_OS_ELEMENY_SIZE

        foa_offset = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * 2 * index
        )
        foa_size = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * (2 * index + 1)
        )
        print(
            f"[+] PYC {target} index: {index:#x}, *offset: {foa_offset:#x}, *size: {foa_size:#x}"
        )

        offset_seg_offset = (
            offset_index + self.config.sizeof_long * 2 * index
        )  # backend 的 offset 在 段内偏移
        offset_seg_size = offset_index + self.config.sizeof_long * (
            2 * index + 1
        )  # backend 的 size 在 段内偏移
        offset = int.from_bytes(
            self.seg_index.content[
                offset_seg_offset : offset_seg_offset + self.config.sizeof_long
            ],
            "little",
        )
        size = int.from_bytes(
            self.seg_index.content[
                offset_seg_size : offset_seg_size + self.config.sizeof_long
            ],
            "little",
        )

        print(f"[+] PYC {target} offset: {offset:#x}, size: {size:#x}")
        return offset, size

    def find_target_os(self, target) -> tuple[int, int]:
        offset_index = self.find_index()
        offset_pstr_start = self.find_pstr_os()

        foa_index = self.display_offset + self.seg_index.offset + offset_index
        va_index = self.binary.imagebase + self.seg_index.virtual_address + offset_index
        print(f"[+] PYC item table foa: {foa_index:#x}, va: {va_index:#x}")
        foa_pstr = self.display_offset + self.seg_pstr_os.offset + offset_pstr_start
        va_pstr = (
            self.binary.imagebase + self.seg_pstr_os.virtual_address + offset_pstr_start
        )
        print(f"[+] PYC string table foa: {foa_pstr:#x}, va: {va_pstr:#x}")

        offset_str = self.seg_str.search(target)
        if offset_str is None:
            raise DataNotFoundError(f'target "{target}" not found')
        va = self.binary.imagebase + self.seg_str.virtual_address + offset_str
        rel = va - va_pstr

        # or search((1 << 32) + rel, size=OS_ELEMENY_SIZE)
        offset_pstr = self.seg_pstr_os.search(
            rel.to_bytes(OS_ELEMENY_SIZE, "little", signed=True)
        )
        if offset_pstr is None:
            raise DataNotFoundError(f'pointer to target "{target}" not found')
        index = (offset_pstr - offset_pstr_start) // OS_ELEMENY_SIZE

        foa_offset = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * 2 * index
        )
        foa_size = (
            self.display_offset
            + self.seg_index.offset
            + offset_index
            + self.config.sizeof_long * (2 * index + 1)
        )
        print(
            f"[+] PYC {target} index: {index:#x}, *offset: {foa_offset:#x}, *size: {foa_size:#x}"
        )

        offset_seg_offset = (
            offset_index + self.config.sizeof_long * 2 * index
        )  # backend 的 offset 在 段内偏移
        offset_seg_size = offset_index + self.config.sizeof_long * (
            2 * index + 1
        )  # backend 的 size 在 段内偏移
        offset = int.from_bytes(
            self.seg_index.content[
                offset_seg_offset : offset_seg_offset + self.config.sizeof_long
            ],
            "little",
        )
        size = int.from_bytes(
            self.seg_index.content[
                offset_seg_size : offset_seg_size + self.config.sizeof_long
            ],
            "little",
        )

        print(f"[+] PYC {target} offset: {offset:#x}, size: {size:#x}")
        return offset, size

    def find_target(self, target) -> tuple[int, int]:
        try:
            return self.find_target_no_os(target)
        except:
            return self.find_target_os(target)


class PEHelper(HelperBase):
    binary: lief.PE.Binary

    def __init__(self, path):
        super().__init__()
        self.binary = lief.PE.parse(path)  # type:ignore
        self.config = PE_CONFIG
        self.display_offset = 0


class ELFHelper(HelperBase):
    binary: lief.ELF.Binary

    def __init__(self, path):
        super().__init__()
        self.binary = lief.ELF.parse(path)  # type:ignore
        self.config = ELF_CONFIG
        self.display_offset = 0


class MachOHelper(HelperBase):
    binary: lief.MachO.Binary
    fat_binary: lief.MachO.FatBinary

    def __init__(self, path):
        super().__init__()
        self.fat_binary = lief.MachO.parse(path)  # type:ignore
        self.binary = self.fat_binary.at(0)
        self.config = MACHO_CONFIG
        self.display_offset = self.binary.fat_offset


@click.command()
@click.argument("launcher", type=click.Path(exists=True), required=True)
@click.argument("target", type=click.Path(exists=False), required=True)
@click.option(
    "os", "-o", "--os", type=click.Choice(["win", "linux", "mac"]), default="win"
)
def cli_find(launcher: str, target: str, os: str):
    find(launcher, target, os)


def find(launcher: str, target: str, os: str = "win") -> tuple[int, int]:
    if os == "win":
        exe = PEHelper(launcher)
    elif os == "linux":
        exe = ELFHelper(launcher)
    elif os == "mac":
        exe = MachOHelper(launcher)
    else:
        raise ValueError(f"Unknow os: {os}")
    offset, size = exe.find_target(target)

    return offset, size


if __name__ == "__main__":
    cli_find()
