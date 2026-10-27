"""Identity tests on the base disc: every rebuild without edits must reproduce the original bytes (or rows).

  python tools/ace2/test_identity.py            all checks (reads the whole DATA.BIN, packs a sample)
  python tools/ace2/test_identity.py --pack-all also LZSS-repacks every packed resource (slow)
"""
import argparse, collections, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ace2lib import BASE, BASE_EXE, Disc, inner_entries, inner_rebuild, try_unpack, unpack, pack, TextTable, \
    mission_container, mission_table, mission_relayout, small_tables, require, u32, vmd_chunks, vmd_replace, VMD_TEXT


def walk(data, path, depth, visit):
    """Visit every nested payload: inner binders and LZSS-packed resources are opened recursively."""
    visit(path, data)
    plain = try_unpack(data) if depth < 4 else None
    if plain is not None:
        walk(plain, path + ':lz', depth + 1, visit)
        return
    rows = inner_entries(data)
    if rows and depth < 4:
        for e, a, b in rows:
            walk(data[a:b], '%s/%d' % (path, e), depth + 1, visit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pack-all', action='store_true')
    args = ap.parse_args()
    disc = Disc(BASE)
    require(BASE_EXE in disc.files, 'Expected the Special Vocal Version disc (%s)' % BASE_EXE)
    idx = disc.index
    offsets, total = idx.layout({e[0]: e[2] for e in idx.entries})
    require(total == disc.data_file['size'] == idx.size, 'DATA.BIN total size %d vs %d' % (total, disc.data_file['size']))
    require(all(offsets[e[0]] == (e[1], e[2]) for e in idx.entries), 'DATA.BIN layout differs')
    require(idx.header_for(offsets, total) == idx.head, 'DATA.BIN header differs')
    print('PASS DATA.BIN index/layout identity (%d entries, %d bytes)' % (len(idx.entries), total), flush=True)

    stats = collections.Counter()
    packed = []

    def visit(path, data):
        rows = inner_entries(data)
        if rows:
            require(inner_rebuild(data, {}) == data, 'inner rebuild differs at ' + path)
            stats['inner binders'] += 1
        if try_unpack(data) is not None:
            packed.append((path, len(data)))
            stats['packed'] += 1
        chunks = vmd_chunks(data)
        if chunks:
            for at, magic, size in chunks:
                if magic in VMD_TEXT:
                    require(vmd_replace(data, magic, lambda table: table) == data, 'VMD identity at %s %r' % (path, magic))
                    t = TextTable(data[at + 16:at + size])
                    new = vmd_replace(data, magic, lambda table: TextTable(table).rebuild({}))
                    require(vmd_chunks(new) is not None, 'VMD chain after rebuild at ' + path)
                    stats['partner package tables'] += 1
                    stats['rows'] += len(t.rows)
            return
        if mission_container(data):
            mt = mission_table(data)
            if mt:
                at, table = mt
                require(mission_relayout(data, {at: data[at:at + table.size]}) == data, 'mission relayout identity at ' + path)
                new = mission_relayout(data, {at: table.rebuild({})})
                require(TextTable(new[u32(new, 20):]).rows == table.rows, 'mission relayout rows at ' + path)
                stats['mission containers'] += 1
                stats['rows'] += len(table.rows)
            else:
                stats['mission containers without dialogue'] += 1
            subs = small_tables(data)
            require(mission_relayout(data, {off: data[off:off + t.size] for sid, off, t in subs}) == data,
                    'mission relayout identity of sub-tables at ' + path)
            for sid, off, t in subs:
                require(TextTable(t.rebuild({})).rows == t.rows, 'sub-table rebuild at %s/%d' % (path, sid))
                stats['mission sub-tables'] += 1
        elif data[:4] == b'\0\0\1\0':
            try:
                t = TextTable(data)
            except (ValueError, UnicodeError):
                return
            require(TextTable(t.rebuild({})).rows == t.rows, 'table rebuild at ' + path)
            stats['text tables'] += 1
            stats['rows'] += len(t.rows)

    t0 = time.time()
    for rid in disc.ids():
        if disc.index.by_id[rid][2] > 64 << 20:
            stats['skipped >64MB'] += 1
            continue
        walk(disc.get(rid), str(rid), 0, visit)
    print('PASS nested identity in %.0fs: %s' % (time.time() - t0, dict(stats)), flush=True)

    sample = packed if args.pack_all else sorted(packed, key=lambda p: p[1])[:: max(1, len(packed) // 12)]
    t0 = time.time()
    for path, _ in sample:
        top = int(path.split('/')[0].split(':')[0])
        data = disc.get(top)
        for part in path.split('/')[1:]:
            data = next(data[a:b] for e, a, b in inner_entries(data) if str(e) == part.split(':')[0])
        plain = unpack(data)
        require(unpack(pack(plain)) == plain, 'LZSS round trip ' + path)
    print('PASS LZSS round trip on %d of %d packed resources (%.0fs)' % (len(sample), len(packed), time.time() - t0))


if __name__ == '__main__':
    main()
