# Made by Claude Ai & Relic Hunter
import os
import struct
import sys

SEC_RVA = 0x1000
SEC_RAW = 0x200
SEC_SIZE = 0x400
IMPORTS = ["GetModuleHandleW", "VirtualProtect", "SleepEx", "GetCurrentProcess", "FlushInstructionCache"]
DATA = {"entry_ptr": 0x180, "saved": 0x188, "old_protect": 0x198}
IMPORT_DIR = 0x200
ILT = 0x230
IAT = ILT + 8 * (len(IMPORTS) + 1)
NAMES = IAT + 8 * (len(IMPORTS) + 1)


class Asm:
    def __init__(self, base):
        self.base = base
        self.code = bytearray()
        self.labels = {}
        self.fix = []

    def here(self):
        return self.base + len(self.code)

    def b(self, *parts):
        for p in parts:
            self.code += bytes(p) if isinstance(p, (list, tuple)) else p

    def rip(self, prefix, target, tail=b""):
        self.code += prefix
        pos = len(self.code)
        self.code += b"\0\0\0\0" + tail
        self.fix.append((pos, target, len(tail)))

    def label(self, name):
        self.labels[name] = self.here()

    def jcc8(self, op, name):
        self.code += bytes([op, 0])
        self.fix.append((len(self.code) - 1, ("rel8", name), 0))

    def resolve(self, addr_of):
        for pos, target, tail in self.fix:
            if isinstance(target, tuple):
                rel = self.labels[target[1]] - (self.base + pos + 1)
                assert -128 <= rel < 128
                self.code[pos] = rel & 0xFF
            else:
                nxt = self.base + pos + 4 + tail
                struct.pack_into("<i", self.code, pos, addr_of(target) - nxt)
        return bytes(self.code)


def iat(name):
    return SEC_RVA + IAT + 8 * IMPORTS.index(name)


def addr_of(target):
    if target in IMPORTS:
        return iat(target)
    if target in DATA:
        return SEC_RVA + DATA[target]
    if target == "trampoline":
        return SEC_RVA + 0x100
    raise KeyError(target)


def dllmain():
    a = Asm(SEC_RVA)
    a.b([0x83, 0xFA, 0x01])
    a.jcc8(0x74, "body")
    a.b([0xB8, 0x01, 0, 0, 0], [0xC3])
    a.label("body")
    a.b([0x53], [0x48, 0x83, 0xEC, 0x30], [0x31, 0xC9])
    a.rip(b"\xFF\x15", "GetModuleHandleW")
    a.b([0x8B, 0x48, 0x3C], [0x8B, 0x4C, 0x08, 0x28], [0x48, 0x01, 0xC8], [0x48, 0x89, 0xC3])
    a.rip(b"\x48\x89\x05", "entry_ptr")
    a.b([0x48, 0x89, 0xD9], [0xBA, 0x10, 0, 0, 0], [0x41, 0xB8, 0x40, 0, 0, 0])
    a.rip(b"\x4C\x8D\x0D", "old_protect")
    a.rip(b"\xFF\x15", "VirtualProtect")
    a.b([0x85, 0xC0])
    a.jcc8(0x74, "done")
    a.b([0x48, 0x8B, 0x03])
    a.rip(b"\x48\x89\x05", "saved")
    a.b([0x8B, 0x43, 0x08])
    a.code += b"\x89\x05"
    pos = len(a.code)
    a.code += b"\0\0\0\0"
    a.fix.append((pos, "saved+8", 0))
    a.rip(b"\x48\x8D\x05", "trampoline")
    a.b([0x66, 0xC7, 0x03, 0x48, 0xB8], [0x48, 0x89, 0x43, 0x02], [0x66, 0xC7, 0x43, 0x0A, 0xFF, 0xE0])
    a.rip(b"\xFF\x15", "GetCurrentProcess")
    a.b([0x48, 0x89, 0xC1], [0x48, 0x89, 0xDA], [0x41, 0xB8, 0x0C, 0, 0, 0])
    a.rip(b"\xFF\x15", "FlushInstructionCache")
    a.label("done")
    a.b([0x48, 0x83, 0xC4, 0x30], [0x5B])
    a.b([0xB8, 0x01, 0, 0, 0], [0xC3])
    return a.resolve(lambda t: addr_of(t) if t != "saved+8" else SEC_RVA + DATA["saved"] + 8)


def trampoline():
    a = Asm(SEC_RVA + 0x100)
    a.b([0x51], [0x52], [0x41, 0x50], [0x41, 0x51], [0x56], [0x57], [0x48, 0x83, 0xEC, 0x28])
    a.b([0x31, 0xC9], [0xBA, 0x01, 0, 0, 0])
    a.rip(b"\xFF\x15", "SleepEx")
    a.rip(b"\x48\x8B\x3D", "entry_ptr")
    a.rip(b"\x48\x8D\x35", "saved")
    a.b([0xB9, 0x0C, 0, 0, 0], [0xF3, 0xA4], [0x48, 0x83, 0xC4, 0x28])
    a.b([0x5F], [0x5E], [0x41, 0x59], [0x41, 0x58], [0x5A], [0x59])
    a.rip(b"\xFF\x25", "entry_ptr")
    return a.resolve(addr_of)


def section():
    s = bytearray(SEC_SIZE)
    main = dllmain()
    tramp = trampoline()
    assert len(main) <= 0x100 and len(tramp) <= 0x80
    s[0:len(main)] = main
    s[0x100:0x100 + len(tramp)] = tramp
    name_rvas = []
    off = NAMES
    for name in IMPORTS:
        name_rvas.append(SEC_RVA + off)
        entry = b"\0\0" + name.encode() + b"\0"
        if len(entry) % 2:
            entry += b"\0"
        s[off:off + len(entry)] = entry
        off += len(entry)
    dll_name_rva = SEC_RVA + off
    s[off:off + 13] = b"KERNEL32.dll\0"
    off += 13
    assert off <= SEC_SIZE
    for i, rva in enumerate(name_rvas):
        struct.pack_into("<Q", s, ILT + 8 * i, rva)
        struct.pack_into("<Q", s, IAT + 8 * i, rva)
    struct.pack_into("<IIIII", s, IMPORT_DIR, SEC_RVA + ILT, 0, 0, dll_name_rva, SEC_RVA + IAT)
    return bytes(s)


def build(path):
    dos = bytearray(0x40)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x40)
    coff = struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 0xF0, 0x2022)
    dirs = [(0, 0)] * 16
    dirs[1] = (SEC_RVA + IMPORT_DIR, 40)
    dirs[12] = (SEC_RVA + IAT, 8 * (len(IMPORTS) + 1))
    opt = struct.pack(
        "<HBBIIIIIQIIHHHHHHIIIIHHQQQQII",
        0x20B, 14, 0, SEC_SIZE, 0, 0, SEC_RVA, SEC_RVA, 0x180000000, 0x1000, 0x200,
        6, 0, 0, 0, 6, 0, 0, 0x2000, 0x200, 0, 2, 0x0100,
        0x100000, 0x1000, 0x100000, 0x1000, 0, 16,
    ) + b"".join(struct.pack("<II", *d) for d in dirs)
    assert len(opt) == 0xF0
    sect = b".text\0\0\0" + struct.pack("<IIIIIIHHI", SEC_SIZE, SEC_RVA, SEC_SIZE, SEC_RAW, 0, 0, 0, 0, 0xE0000060)
    head = bytes(dos) + b"PE\0\0" + coff + opt + sect
    head += b"\0" * (SEC_RAW - len(head))
    data = head + section()
    with open(path, "wb") as f:
        f.write(data)
    print(path, len(data), "bytes")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin", "rsdragonwilds_ue4ss_boot.dll"
    )
    build(out)
