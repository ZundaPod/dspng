#!/usr/bin/env python3
"""
Compile .po translation files to .mo binary format for gettext.

Usage:
    uv run scripts/compile_locales.py          # compile all locales
    uv run scripts/compile_locales.py zh_CN    # compile one locale
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = PROJECT_ROOT / "locales"

# .mo magic number (little-endian)
_MAGIC = 0x950412DE


def _read_po(po_path: Path) -> dict[str, str]:
    """Parse a simple .po file into {msgid: msgstr}.  Handles multi-line
    strings and escaped quotes but not plural forms or fuzzy flags."""
    entries: dict[str, str] = {}
    msgid: list[str] = []
    msgstr: list[str] = []
    state = None  # "id" | "str"

    for raw in po_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith('msgid "'):
            if msgid and state:
                # Flush previous entry.
                key = "".join(msgid)
                if key or msgstr:
                    entries[key] = "".join(msgstr)
                msgid.clear()
                msgstr.clear()
            msgid.append(_unescape(line[7:-1]))
            state = "id"
        elif line.startswith('msgstr "'):
            msgstr.append(_unescape(line[8:-1]))
            state = "str"
        elif line.startswith('"') and state == "id":
            msgid.append(_unescape(line[1:-1]))
        elif line.startswith('"') and state == "str":
            msgstr.append(_unescape(line[1:-1]))

    # Flush the last entry.
    key = "".join(msgid)
    # Always include entries, even the empty-msgid header (contains charset).
    if key or msgstr:
        entries[key] = "".join(msgstr)

    return entries


def _unescape(s: str) -> str:
    """Unescape common .po escape sequences."""
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")


def _write_mo(entries: dict[str, str], mo_path: Path):
    """Write a .mo binary file from a {msgid: msgstr} dict."""
    # Sort by msgid for deterministic output.
    ids = sorted(entries.keys())
    n = len(ids)

    # Build string data.
    id_data: list[bytes] = []
    str_data: list[bytes] = []
    for i in ids:
        id_data.append(i.encode("utf-8") + b"\x00")
        str_data.append(entries[i].encode("utf-8") + b"\x00")

    # Compute offsets.
    header_size = (
        28  # magic(4) + rev(4) + n(4) + o_tab(4) + t_tab(4) + hash_sz(4) + hash_off(4)
    )
    desc_size = n * 8  # 4 bytes length + 4 bytes offset per string
    id_off = header_size + desc_size * 2  # original table + translation table
    str_off = id_off

    # Build descriptor tables.
    orig_table = bytearray()
    trans_table = bytearray()
    orig_data = bytearray()
    trans_data = bytearray()

    for i in range(n):
        orig_table += struct.pack("<II", len(id_data[i]) - 1, str_off + len(orig_data))
        orig_data += id_data[i]

    str_off += len(orig_data)
    for i in range(n):
        trans_table += struct.pack(
            "<II", len(str_data[i]) - 1, str_off + len(trans_data)
        )
        trans_data += str_data[i]

    o_off = header_size
    t_off = header_size + desc_size

    with mo_path.open("wb") as f:
        f.write(struct.pack("<I", _MAGIC))
        f.write(struct.pack("<I", 0))  # revision
        f.write(struct.pack("<I", n))
        f.write(struct.pack("<I", o_off))
        f.write(struct.pack("<I", t_off))
        f.write(struct.pack("<I", 0))  # hash table size (none)
        f.write(struct.pack("<I", 0))  # hash table offset
        f.write(orig_table)
        f.write(trans_table)
        f.write(orig_data)
        f.write(trans_data)


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else None

    locales = [target] if target else ["en", "zh_CN"]
    for code in locales:
        po = LOCALES_DIR / code / "LC_MESSAGES" / "messages.po"
        mo = LOCALES_DIR / code / "LC_MESSAGES" / "messages.mo"
        if not po.exists():
            print(f"  SKIP {code}: {po} not found")
            continue
        entries = _read_po(po)
        _write_mo(entries, mo)
        print(f"  {code}: {len(entries)} strings → {mo}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
