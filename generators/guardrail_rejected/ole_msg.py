"""Minimal, dependency-free writer for Outlook .msg files (MS-CFB v3 + MS-OXMSG layout).

What is written (and how faithful it is):
- A real compound file: 512-byte sectors, FAT, directory with balanced sibling trees, mini FAT and
  mini stream for streams under 4,096 bytes, root CLSID of an IPM.Note message.
- MS-OXMSG structure: top-level ``__properties_version1.0`` (32-byte header + 16-byte entries),
  ``__substg1.0_XXXXYYYY`` streams for every string property (PT_UNICODE, 001F), one recipient
  storage ``__recip_version1.0_#00000000`` with its own property stream, and an empty named-property
  storage ``__nameid_version1.0``.
- Not written: attachments, RTF-compressed body, HTML body, named properties. Outlook-specific
  extras (search keys, entry ids) are omitted, so Outlook may refuse to open the file for editing;
  olefile and MSG text extractors read it.
"""
from __future__ import annotations

import datetime as _dt
import math
import struct
import uuid

FREESECT, ENDOFCHAIN, FATSECT, NOSTREAM = 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFD, 0xFFFFFFFF
SECTOR, MINI, CUTOFF = 512, 64, 4096
IPM_NOTE_CLSID = uuid.UUID("00020D0B-0000-0000-C000-000000000046").bytes_le

PT_LONG, PT_BOOLEAN, PT_SYSTIME, PT_UNICODE = 0x0003, 0x000B, 0x0040, 0x001F
PROPATTR = 0x00000006  # readable | writable


class Node:
    def __init__(self, name: str, kind: str, data: bytes = b"", clsid: bytes = b"\0" * 16):
        assert kind in ("root", "storage", "stream")
        assert len(name) <= 31, name
        self.name, self.kind, self.data, self.clsid = name, kind, data, clsid
        self.children: list[Node] = []
        self.id = self.left = self.right = self.child = NOSTREAM
        self.start, self.size = 0, 0

    def add(self, node: "Node") -> "Node":
        self.children.append(node)
        return node


def _ceil(a: int, b: int) -> int:
    return (a + b - 1) // b


def write_cfb(root: Node) -> bytes:
    entries: list[Node] = []

    def assign(n: Node) -> None:
        n.id = len(entries)
        entries.append(n)
        for c in n.children:
            assign(c)

    assign(root)

    def build(nodes: list[Node]) -> int:
        if not nodes:
            return NOSTREAM
        mid = len(nodes) // 2
        m = nodes[mid]
        m.left, m.right = build(nodes[:mid]), build(nodes[mid + 1:])
        return m.id

    for n in entries:
        if n.kind in ("root", "storage"):
            n.child = build(sorted(n.children, key=lambda c: (len(c.name), c.name.upper())))

    mini, minifat, big = bytearray(), [], []
    for n in entries:
        if n.kind != "stream":
            continue
        size = len(n.data)
        n.size = size
        if size == 0:
            n.start = ENDOFCHAIN
        elif size < CUTOFF:
            n.start = len(mini) // MINI
            k = _ceil(size, MINI)
            minifat += [n.start + i + 1 if i < k - 1 else ENDOFCHAIN for i in range(k)]
            mini += n.data + b"\0" * (k * MINI - size)
        else:
            big.append(n)

    dir_secs = _ceil(len(entries) * 128, SECTOR)
    minifat_secs = _ceil(len(minifat) * 4, SECTOR)
    mini_secs = _ceil(len(mini), SECTOR)
    big_secs = [_ceil(len(n.data), SECTOR) for n in big]
    data_secs = dir_secs + minifat_secs + mini_secs + sum(big_secs)
    fat_secs = 1
    while _ceil(fat_secs + data_secs, SECTOR // 4) > fat_secs:
        fat_secs += 1
    assert fat_secs <= 109, "file too large for a header-only DIFAT"

    fat = [FREESECT] * (fat_secs * (SECTOR // 4))
    sec = 0
    fat_ids = list(range(fat_secs))
    for i in fat_ids:
        fat[i] = FATSECT
    sec += fat_secs

    def chain(start: int, count: int) -> int:
        for k in range(count):
            fat[start + k] = start + k + 1 if k < count - 1 else ENDOFCHAIN
        return start if count else ENDOFCHAIN

    dir_start = chain(sec, dir_secs); sec += dir_secs
    minifat_start = chain(sec, minifat_secs); sec += minifat_secs
    mini_start = chain(sec, mini_secs); sec += mini_secs
    for n, cnt in zip(big, big_secs):
        n.start = chain(sec, cnt)
        sec += cnt
    root.start, root.size = (mini_start, len(mini)) if mini else (ENDOFCHAIN, 0)

    def dirent(n: Node | None) -> bytes:
        if n is None:
            return struct.pack("<64sHBBIII16sIQQIQ", b"", 0, 0, 0, NOSTREAM, NOSTREAM, NOSTREAM, b"\0" * 16,
                               0, 0, 0, 0, 0)
        nm = n.name.encode("utf-16-le") + b"\0\0"
        typ = {"storage": 1, "stream": 2, "root": 5}[n.kind]
        start, size = (n.start, n.size) if n.kind in ("stream", "root") else (0, 0)
        return struct.pack("<64sHBBIII16sIQQIQ", nm, len(nm), typ, 1, n.left, n.right, n.child, n.clsid,
                           0, 0, 0, start, size)

    dir_bytes = b"".join(dirent(n) for n in entries)
    dir_bytes += b"".join(dirent(None) for _ in range(dir_secs * 4 - len(entries)))

    hdr = struct.pack("<8s16sHHHHH6sIIIIIIIII", b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1", b"\0" * 16, 0x003E, 0x0003,
                      0xFFFE, 9, 6, b"\0" * 6, 0, fat_secs, dir_start, 0, CUTOFF,
                      minifat_start, minifat_secs, ENDOFCHAIN, 0)
    hdr += struct.pack("<109I", *(fat_ids + [FREESECT] * (109 - len(fat_ids))))
    assert len(hdr) == SECTOR

    out = bytearray(hdr)
    out += struct.pack(f"<{len(fat)}I", *fat)
    out += dir_bytes
    if minifat_secs:
        mf = minifat + [FREESECT] * (minifat_secs * (SECTOR // 4) - len(minifat))
        out += struct.pack(f"<{len(mf)}I", *mf)
    if mini_secs:
        out += bytes(mini) + b"\0" * (mini_secs * SECTOR - len(mini))
    for n, cnt in zip(big, big_secs):
        out += n.data + b"\0" * (cnt * SECTOR - len(n.data))
    assert len(out) == SECTOR * (1 + sec)
    return bytes(out)


# ---------------------------------------------------------------------------------------------
# MS-OXMSG
# ---------------------------------------------------------------------------------------------

def filetime(d: _dt.datetime) -> int:
    if d.tzinfo is not None:
        d = d.astimezone(_dt.timezone.utc).replace(tzinfo=None)
    return int((d - _dt.datetime(1601, 1, 1)).total_seconds()) * 10_000_000


def _fill(storage: Node, strings: dict[int, str], fixed: list[tuple[int, int, int]], header: bytes) -> None:
    """Add string streams and the property stream to a message or recipient storage.

    strings: {prop_id: text}; fixed: [(prop_id, prop_type, value)].
    """
    entries = []
    for pid, ptype, val in fixed:
        entries.append(struct.pack("<IIQ", (pid << 16) | ptype, PROPATTR, val))
    for pid in sorted(strings):
        data = strings[pid].encode("utf-16-le")
        storage.add(Node(f"__substg1.0_{pid:04X}{PT_UNICODE:04X}", "stream", data))
        entries.append(struct.pack("<IIII", (pid << 16) | PT_UNICODE, PROPATTR, len(data) + 2, 0))
    storage.add(Node("__properties_version1.0", "stream", header + b"".join(entries)))


def build_msg(*, subject: str, body: str, sender_name: str, sender_email: str, to_name: str, to_email: str,
              sent: _dt.datetime, headers: str | None = None) -> bytes:
    """An IPM.Note with one To recipient. ``sent`` must be timezone-aware."""
    body = body.replace("\r\n", "\n").replace("\n", "\r\n")
    root = Node("Root Entry", "root", clsid=IPM_NOTE_CLSID)
    nameid = root.add(Node("__nameid_version1.0", "storage"))
    for pid in (0x0002, 0x0003, 0x0004):
        nameid.add(Node(f"__substg1.0_{pid:04X}0102", "stream", b""))
    recip = root.add(Node("__recip_version1.0_#00000000", "storage"))
    _fill(recip, {
        0x3001: to_name,            # PR_DISPLAY_NAME
        0x3002: "SMTP",             # PR_ADDRTYPE
        0x3003: to_email,           # PR_EMAIL_ADDRESS
        0x39FE: to_email,           # PR_SMTP_ADDRESS
        0x5FF6: to_name,            # PR_RECIPIENT_DISPLAY_NAME
    }, [
        (0x0C15, PT_LONG, 1),       # PR_RECIPIENT_TYPE = MAPI_TO
        (0x3000, PT_LONG, 0),       # PR_ROWID
        (0x0FFE, PT_LONG, 6),       # PR_OBJECT_TYPE = MAPI_MAILUSER
        (0x3900, PT_LONG, 0),       # PR_DISPLAY_TYPE = DT_MAILUSER
    ], b"\0" * 8)
    strings = {
        0x001A: "IPM.Note",         # PR_MESSAGE_CLASS
        0x0037: subject,            # PR_SUBJECT
        0x0E1D: subject.split(": ", 1)[-1] if subject[:4].upper() in ("RE: ", "FW: ") else subject,
        0x0070: subject.split(": ", 1)[-1] if subject[:4].upper() in ("RE: ", "FW: ") else subject,
        0x0042: sender_name,        # PR_SENT_REPRESENTING_NAME
        0x0064: "SMTP",
        0x0065: sender_email,
        0x0C1A: sender_name,        # PR_SENDER_NAME
        0x0C1E: "SMTP",
        0x0C1F: sender_email,
        0x5D01: sender_email,       # PR_SENDER_SMTP_ADDRESS
        0x0E04: to_name,            # PR_DISPLAY_TO
        0x1000: body,               # PR_BODY
    }
    if headers:
        strings[0x007D] = headers.replace("\r\n", "\n").replace("\n", "\r\n")  # PR_TRANSPORT_MESSAGE_HEADERS
    ft = filetime(sent)
    fixed = [
        (0x0017, PT_LONG, 1),             # PR_IMPORTANCE = normal
        (0x0039, PT_SYSTIME, ft),         # PR_CLIENT_SUBMIT_TIME
        (0x0E06, PT_SYSTIME, ft + 30 * 10_000_000),  # PR_MESSAGE_DELIVERY_TIME
        (0x0E07, PT_LONG, 1),             # PR_MESSAGE_FLAGS = MSGFLAG_READ
        (0x340D, PT_LONG, 0x00040000),    # PR_STORE_SUPPORT_MASK = STORE_UNICODE_OK
    ]
    header = b"\0" * 8 + struct.pack("<IIII", 1, 0, 1, 0) + b"\0" * 8
    _fill(root, strings, fixed, header)
    return write_cfb(root)
