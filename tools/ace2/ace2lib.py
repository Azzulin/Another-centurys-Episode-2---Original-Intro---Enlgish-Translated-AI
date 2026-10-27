"""Format library for Another Century's Episode 2 - Special Vocal Version (SLPS-25829).

Adapted from the ACE1 library (D:\\Ace 1\\tools\\ace1\\ace1lib.py), which itself copies codecs from ACE3 0.9.3 (MIT).

Containers
  DATA.BIN index binder    'BND\\0' f7ff0000 d3 | +12 total size | +16 count | +24 0x30800 (kept as is)
                           entries @36: (id, offset, size), ids ascending, payloads 2048-aligned, no names
  inner binder             'BND\\0' | +4 size | +8 count | (id, offset) pairs @16, payloads 32-aligned
  packed                   ACE3 LZSS: 00 01 00 00 | unpacked size BE | 0 | body
  text table               magic 0x10000, size, 0, ranges, count, pointer array, 0 | ranges | pointers | CP932 pool
  mission container        00 01 00 00 | +4 list C (or total size, or 0) | +8 list A | +12 list B | +16 list D | +20
                           dialogue table | +24 second table | +28 counts A, B, D, C (bytes) | +32 last section
                           (48-byte header); an empty list has offset 0 (+8 = 0 gives the LZSS signature: is_packed)
                           and 43 containers have no dialogue table (+20 = 0), only list A
                           lists A, B, D: 16-byte records (id, offset, 0, 0); list A = enemy-name sub-tables
                           list C: (id, name table, 256x128 portrait image, 0)
                           Sections hold no container offsets (twins 6### / 42### carry them byte-identical at other
                           offsets), so a table can grow in place while the sections after it move (mission_relayout).
"""
import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Base disc: every build starts from the untouched Special Vocal Version.
BASE = ROOT / "Another Century's Episode 2 - Special Vocal Version (Japan).iso"
# Original 2006 release: source of the opening movie with "Glorious" only.
ORIGINAL_RELEASE = ROOT / "Another Century's Episode 2 (Japan).iso"
BASE_EXE = '/SLPS_258.29'
SECTOR = 2048


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def require(value, message):
    if not value:
        raise ValueError(message)


def align(value, to):
    return (value + to - 1) // to * to


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- ISO9660

def iso_files(stream):
    """{'/DATA.BIN': {'offset', 'size', 'record'}}; record = absolute offset of the directory record."""
    stream.seek(16 * SECTOR)
    pvd = stream.read(SECTOR)
    require(pvd[:7] == b'\x01CD001\x01', 'Expected ISO9660 primary volume')
    found = {}

    def walk(lba, size, parent):
        stream.seek(lba * SECTOR)
        data = stream.read(size)
        at = 0
        while at < len(data):
            length = data[at]
            if not length:
                at = (at // SECTOR + 1) * SECTOR
                continue
            record = data[at:at + length]
            name = record[33:33 + record[32]]
            if name not in (b'\0', b'\1'):
                full = parent + '/' + name.decode('ascii').split(';')[0]
                if record[25] & 2:
                    walk(u32(record, 2), u32(record, 10), full)
                else:
                    found[full] = {'offset': u32(record, 2) * SECTOR, 'size': u32(record, 10), 'record': lba * SECTOR + at}
            at += length

    walk(u32(pvd, 158), u32(pvd, 166), '')
    return found


# ---------------------------------------------------------------- DATA.BIN

class DataBin:
    """DATA.BIN index. Payload order and 2048 alignment are preserved on rebuild."""
    HEAD = 36
    MAGIC = b'BND\0\xff\xf7\0\0'

    def __init__(self, head, entries, size):
        self.head, self.entries, self.size = head, entries, size
        self.by_id = {e[0]: e for e in entries}

    @classmethod
    def read_index(cls, stream, base):
        stream.seek(base)
        top = stream.read(cls.HEAD)
        require(top[:8] == cls.MAGIC, 'Not an ACE2 DATA.BIN')
        count = u32(top, 16)
        stream.seek(base)
        probe = stream.read(cls.HEAD + count * 12)
        entries = [struct.unpack_from('<3I', probe, cls.HEAD + i * 12) for i in range(count)]
        require([e[0] for e in entries] == sorted(e[0] for e in entries), 'DATA.BIN ids not ascending')
        first = min(e[1] for e in entries)
        stream.seek(base)
        return cls(stream.read(first), entries, u32(top, 12))

    def layout(self, sizes):
        """New (offset, size) per id, original payload order, 2048-aligned. Returns (offsets, total)."""
        order = sorted(self.entries, key=lambda e: e[1])
        cursor = order[0][1]
        require(cursor >= self.HEAD + len(self.entries) * 12, 'Index overlaps payloads')
        result = {}
        for i, e in enumerate(order):
            size = sizes[e[0]]
            result[e[0]] = (cursor, size)
            cursor = cursor + size if i + 1 == len(order) else align(cursor + size, SECTOR)
        return result, cursor

    def header_for(self, offsets, total):
        head = bytearray(self.head)
        struct.pack_into('<I', head, 12, total)
        for i, e in enumerate(self.entries):
            off, size = offsets[e[0]]
            struct.pack_into('<II', head, self.HEAD + i * 12 + 4, off, size)
        return bytes(head)


class Disc:
    """Read-only access to a disc image and its DATA.BIN resources."""

    def __init__(self, path=BASE):
        self.path = Path(path)
        self.stream = self.path.open('rb')
        self.files = iso_files(self.stream)
        self.data_file = self.files['/DATA.BIN']
        self.index = DataBin.read_index(self.stream, self.data_file['offset'])

    def get(self, rid):
        _, off, size = self.index.by_id[rid]
        self.stream.seek(self.data_file['offset'] + off)
        return self.stream.read(size)

    def ids(self):
        return [e[0] for e in self.index.entries]

    def close(self):
        self.stream.close()


# ---------------------------------------------------------------- inner binder

def inner_entries(data):
    if data[:4] != b'BND\0' or len(data) < 16 or u32(data, 4) != len(data):
        return None
    count = u32(data, 8)
    if not 0 < count < 4096 or 16 + count * 8 > len(data):
        return None
    rows = [struct.unpack_from('<II', data, 16 + i * 8) for i in range(count)]
    out = []
    for n, (eid, off) in enumerate(rows):
        end = rows[n + 1][1] if n + 1 < count else len(data)
        if not (16 + count * 8 <= off <= end <= len(data)):
            return None
        out.append((eid, off, end))
    return out


def inner_get(data, eid):
    return next(data[a:b] for e, a, b in inner_entries(data) if e == eid)


def inner_rebuild(data, replace):
    """Rebuild an inner binder; every payload but the last is padded to 32 like the original."""
    rows = inner_entries(data)
    require(rows is not None, 'Not an inner binder')
    out = bytearray(data[:rows[0][1]])
    for n, (eid, start, end) in enumerate(rows):
        struct.pack_into('<I', out, 16 + n * 8 + 4, len(out))
        payload = replace.get(eid, data[start:end])
        out.extend(payload)
        if n + 1 < len(rows):
            out.extend(bytes(align(len(out), 32) - len(out)))
    struct.pack_into('<I', out, 4, len(out))
    return bytes(out)


# ---------------------------------------------------------------- LZSS (ACE3 tools/packed_resource.py, MIT)

PACK_MAGIC = b'\x00\x01\x00\x00'
WINDOW, MAX_LEN = 4096, 16


def is_packed(data, size=None):
    """LZSS signature with a size the stream can produce (size = whole resource when data is only its head). LZSS
    writes at most 8 x 16 bytes per 17 input bytes; a larger declared size is a mission container whose list A is
    empty (+8 = 0, same signature): Op 04-01 (6041/42041) and 6907 went untranslated through 0.0.16."""
    return len(data) >= 12 and data[:4] == PACK_MAGIC and data[8:12] == b'\0\0\0\0' and \
        struct.unpack('>I', data[4:8])[0] <= 8 * (len(data) if size is None else size)


def unpack(data):
    require(is_packed(data), 'Not a packed resource')
    size = struct.unpack('>I', data[4:8])[0]
    out = bytearray()
    at = 12
    while len(out) < size:
        flags = data[at]; at += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags >> bit & 1:
                b0, b1 = data[at], data[at + 1]; at += 2
                field = b0 << 4 | b1 >> 4
                source = field if len(out) < WINDOW else len(out) - WINDOW + field
                for k in range((b1 & 15) + 1):
                    out.append(out[source + k] if source + k < len(out) else 0)
            else:
                out.append(data[at]); at += 1
    return bytes(out)


def try_unpack(data):
    """Unpacked bytes, or None when the LZSS signature is a false positive (truncated stream)."""
    if not is_packed(data):
        return None
    try:
        return unpack(data)
    except IndexError:
        return None


def pack(plain, align_to=16):
    out = bytearray(PACK_MAGIC + struct.pack('>I', len(plain)) + b'\0\0\0\0')
    chains, n, at = {}, len(plain), 0
    flag_at, bit, items = None, 8, bytearray()

    def insert(p):
        if p + 3 <= n:
            chains.setdefault(plain[p:p + 3], []).append(p)

    while at < n:
        best_len, best_src = 0, 0
        if at + 3 <= n:
            candidates = chains.get(plain[at:at + 3], ())
            limit = min(MAX_LEN, n - at)
            for p in reversed(candidates[-64:]):
                if at - p > WINDOW:
                    break
                k = 3
                while k < limit and plain[p + k] == plain[at + k]:
                    k += 1
                if k > best_len:
                    best_len, best_src = k, p
                    if k == limit:
                        break
        if bit == 8:
            out += items; items = bytearray(); flag_at = len(out); out.append(0); bit = 0
        if best_len >= 3:
            field = best_src if at < WINDOW else WINDOW - (at - best_src)
            out[flag_at] |= 1 << bit
            items += bytes([field >> 4, (field & 15) << 4 | (best_len - 1)])
            for p in range(at, at + best_len):
                insert(p)
            at += best_len
        else:
            items.append(plain[at]); insert(at); at += 1
        bit += 1
    out += items
    out += bytes(-len(out) % align_to)
    return bytes(out)


# ---------------------------------------------------------------- text tables

class TextTable:
    def __init__(self, data):
        require(len(data) >= 40, 'Short text table')
        magic, size, zero, ranges, count, pointers, reserved = struct.unpack_from('<7I', data)
        require(magic == 0x10000 and zero == reserved == 0, 'Not a text table')
        require(0 < ranges < 4096 and pointers == 28 + ranges * 12 and pointers + count * 4 <= size <= len(data), 'Bad table layout')
        ids = []
        for i in range(ranges):
            base, first, last = struct.unpack_from('<3I', data, 28 + i * 12)
            require(base == len(ids) and first <= last, 'Bad ID range')
            ids.extend(range(first, last + 1))
        require(len(ids) == count, 'Slot count mismatch')
        self.data, self.size, self.pointers, self.ids = bytes(data[:size]), size, pointers, ids
        self.rows = {}
        for slot, tid in enumerate(ids):
            p = u32(data, pointers + slot * 4)
            if p:
                end = data.index(b'\0', p, size)
                self.rows[tid] = data[p:end].decode('cp932')

    def rebuild(self, texts):
        """New table with replaced rows; identical strings share one pool entry; size padded to 32."""
        head_end = self.pointers + len(self.ids) * 4
        out = bytearray(self.data[:head_end])
        pool = {}
        for slot, tid in enumerate(self.ids):
            if tid not in self.rows:
                continue
            raw = texts.get(tid, self.rows[tid]).encode('cp932')
            require(b'\0' not in raw, 'NUL in text')
            if raw not in pool:
                pool[raw] = len(out); out.extend(raw + b'\0')
            struct.pack_into('<I', out, self.pointers + slot * 4, pool[raw])
        out.extend(bytes(align(len(out), 32) - len(out)))
        struct.pack_into('<I', out, 4, len(out))
        check = TextTable(out)
        require(check.rows == {t: texts.get(t, s) for t, s in self.rows.items()}, 'Table round-trip failed')
        return bytes(out)


def mission_table(data):
    """(offset, TextTable) of a mission container's active dialogue table, or None."""
    if data[:4] != b'\0\1\0\0' or len(data) < 32 or is_packed(data):
        return None
    at = u32(data, 20)
    try:
        return at, TextTable(data[at:])
    except (ValueError, UnicodeError, struct.error):
        return None


def mission_fields(data):
    """Positions of the words of a mission container that hold an offset ('off') or its total size ('size').
    Two header layouts: lists from 0x20 (+4 = total size when there is no list C) or from 0x30 (+32 = last section).
    The first list starts right after the header; list A may be empty (+8 = 0: 6041, 42041, 6907)."""
    h = struct.unpack_from('<9I', data)
    counts = data[28:32]
    first = min([v for v in h[2:5] if v] + ([h[1]] if counts[3] else []), default=0)
    require(first in (0x20, 0x30), 'Unknown mission container header')
    short = first == 0x20
    fields = [(4, 'size' if short and not counts[3] else 'off')] + [(at, 'off') for at in (8, 12, 16, 20, 24)]
    if not short:
        fields.append((32, 'off'))
    lists = [(h[2], counts[0], (4,)), (h[3], counts[1], (4,)), (h[4], counts[2], (4,))]
    if counts[3]:
        lists.append((h[1], counts[3], (4, 8)))
    for start, n, words in lists:
        if start:
            fields.extend((start + 16 * i + w, 'off') for i in range(n) for w in words)
    return fields


def mission_relayout(data, replace):
    """Mission container with text tables replaced where they are: replace = {table offset: new table bytes}.
    Each new table takes the place of the old one, whatever its size; every byte after it moves by the difference and
    every offset field follows (mission_fields). The Japanese table does not stay behind as dead weight: the
    container is loaded whole into the game's single memory arena, which has no room to spare (ESTUDO 8.6)."""
    fields = mission_fields(data)
    regions = []
    for off, new in sorted(replace.items()):
        old = TextTable(data[off:]).size
        require((len(new) - old) % 16 == 0, 'Table size change breaks the 16-byte alignment of later sections')
        require(not regions or regions[-1][1] <= off, 'Overlapping tables in mission container')
        regions.append((off, off + old, new))

    def move(v):
        shift = 0
        for a, b, new in regions:
            if v >= b:
                shift += len(new) - (b - a)
            else:
                require(v <= a, 'Offset 0x%x points inside a replaced table' % v)
        return v + shift

    out = bytearray()
    pos = 0
    for a, b, new in regions:
        out += data[pos:a] + new
        pos = b
    out += data[pos:]
    patched = set()
    for at, kind in fields:
        v = u32(data, at)
        if kind == 'size' and v:                 # 0 in some containers without dialogue (6904, 6999)
            require(v == len(data), 'Mission container size field mismatch')
            struct.pack_into('<I', out, move(at), len(out))
        elif v:
            struct.pack_into('<I', out, move(at), move(v))
        patched.add(move(at))
    # everything but the replaced tables and the offset fields is the original, moved
    pos = 0
    for a, b, new in regions + [(len(data), len(data), b'')]:
        seg_old, seg_new = bytearray(data[pos:a]), bytearray(out[move(pos):move(pos) + a - pos])
        for p in patched:
            if move(pos) <= p < move(pos) + a - pos:
                seg_old[p - move(pos):p - move(pos) + 4] = seg_new[p - move(pos):p - move(pos) + 4] = b'\0\0\0\0'
        require(seg_old == seg_new, 'Mission container bytes changed outside the replaced tables')
        pos = b
    return bytes(out)


# ---------------------------------------------------------------- VMD model packages

# Text chunks of a partner model package (O:\sr\model\partner\pNNN): PMS = the partner's battle chatter, PPN1/PPN2 =
# pilot names. Each holds a 16-byte chunk header and a text table; the bytes after the table are leftover strings
# no pointer reaches (kept as they are). FNM (model name, in every model) is not included.
VMD_TEXT = (b'PMS\0', b'PPN1', b'PPN2')


def vmd_chunks(data):
    """[(offset, magic, size)] of the top-level chunks of a VMD package ('VMD\\0' ... 'END\\0'), or None. The game walks
    the chain by sizes (no chunk offset is stored anywhere), chunks start 16-aligned."""
    if data[:4] != b'VMD\0':
        return None
    out, at = [], 0
    while at < len(data):
        if at + 16 > len(data):
            return None
        magic, size = data[at:at + 4], u32(data, at + 4)
        if size < 16 or at + size > len(data):
            return None
        out.append((at, magic, size))
        at = align(at + size, 16)
    return out if at == len(data) else None


def vmd_replace(data, magic, fn):
    """VMD package with the text table of chunk `magic` replaced by fn(table bytes); the chunk grows or shrinks with
    it and every later chunk moves (nothing else changes)."""
    chunks = vmd_chunks(data)
    require(chunks is not None, 'Not a VMD package')
    at, _, size = next(c for c in chunks if c[1] == magic)
    table = TextTable(data[at + 16:at + size])
    new = fn(data[at + 16:at + 16 + table.size])
    require((len(new) - table.size) % 16 == 0, 'VMD text table size change breaks chunk alignment')
    chunk = bytearray(data[at:at + 16] + new + data[at + 16 + table.size:at + size])
    struct.pack_into('<I', chunk, 4, len(chunk))
    out = data[:at] + bytes(chunk) + data[at + size:]
    after = vmd_chunks(out)
    require(after is not None and [(m, s) for _, m, s in after if m != magic] == [(m, s) for _, m, s in chunks if m != magic],
            'VMD chunk chain changed')
    return out


def mission_container(data):
    """True for a mission container, with or without a dialogue table (6036, 6330-6336, 6362, 6925, 6970 and twins
    hold enemy names only, +20 = 0)."""
    if data[:4] != b'\0\1\0\0' or len(data) < 48 or is_packed(data):
        return False
    try:
        mission_fields(data)
    except (ValueError, struct.error):
        return False
    return bool(mission_table(data) or small_tables(data))


def mission_text_bytes(data):
    """Bytes taken by the dialogue table and the enemy-name sub-tables of a mission container. A rebuilt container
    must grow exactly by the growth of this number (no dead tables left in the game's memory arena)."""
    mt = mission_table(data)
    sizes = {mt[0]: mt[1].size} if mt else {}
    sizes.update((off, st.size) for sid, off, st in small_tables(data))
    return sum(sizes.values())


def list_a(data):
    """(id, offset) records of list A of a mission container: the first at +8, their count in byte +28. Reading up
    to +12 instead (through 0.0.16) found nothing whenever list B is empty (+12 = 0): 96 containers kept their enemy
    names in Japanese."""
    first = u32(data, 8)
    return [struct.unpack_from('<II', data, first + 16 * i) for i in range(data[28] if first else 0)]


def small_tables(data):
    """Sub-tables of list A of a mission container (enemy names on the lock-on HUD)."""
    out = []
    for sid, off in list_a(data):
        try:
            out.append((sid, off, TextTable(data[off:])))
        except (ValueError, UnicodeError, struct.error):
            pass
    return out
