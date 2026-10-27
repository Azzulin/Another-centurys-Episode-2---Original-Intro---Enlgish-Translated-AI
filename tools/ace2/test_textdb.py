"""Write-back stress test over every text location on the disc (no image is written).

Every exported row gets a synthetic ASCII translation about 1.5x the bytes of its Japanese source, keeping the control
tokens in order. Every touched resource is rebuilt with textdb.patch_resource and then checked:
  - each copy's table parses and carries exactly the synthetic rows (untouched rows unchanged)
  - mission containers grow exactly by the growth of their text tables (no dead Japanese table left behind; the
    non-text bytes themselves are checked by ace2lib.mission_relayout)
  - the disc plan still fits the image (DATA.BIN growth absorbed by the empty tail)
"""
import collections, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ace2lib import BASE, Disc, TextTable, mission_table, mission_text_bytes, small_tables, inner_entries, unpack, require, \
    vmd_chunks
from textdb import discover, group, patch_resource, _split, TOKEN, JPC
from export_text import wanted
from disc import plan


def synthetic(jp):
    """Same tokens in the same order, ASCII filler ~1.5x the Japanese byte length."""
    parts, out = TOKEN.split(jp), []
    tokens = TOKEN.findall(jp)
    for i, p in enumerate(parts):
        lines = p.split('\n')
        out.append('\n'.join(('W' * max(1, len(l.encode('cp932')) * 3 // 2) if l else '') for l in lines))
        if i < len(tokens):
            out.append(tokens[i])
    return ''.join(out)


def locate(data, parts):
    for p in parts:
        if p == ':lz':
            data = unpack(data)
        elif p.startswith(':'):
            break
        else:
            data = next(data[a:b] for e, a, b in inner_entries(data) if e == int(p))
    return data


def main():
    disc = Disc(BASE)
    found = discover(disc)
    groups = group(found)
    texts = {name: {jp: synthetic(jp) for loc, t in members for jp in t.rows.values() if wanted(jp)} for name, members in groups.items()}
    name_of = {loc: name for name, members in groups.items() for loc, _ in members}
    by_resource = collections.defaultdict(list)
    for loc in name_of:
        by_resource[_split(loc)[0]].append(loc)
    new = {}
    for rid, locs in by_resource.items():
        data = disc.get(rid)
        out = patch_resource(data, locs, lambda loc: texts[name_of[loc]])
        if out != data:
            new[rid] = out
    checked = collections.Counter()
    original = dict(found)
    for loc, name in name_of.items():
        rid, parts = _split(loc)
        data = locate(new.get(rid, disc.get(rid)), parts)
        before = original[loc].rows
        expect = {tid: texts[name].get(jp, jp) for tid, jp in before.items()}
        if parts and parts[-1] == ':m':
            got = mission_table(data)[1].rows
            src = locate(disc.get(rid), parts)
            require(len(data) - len(src) == mission_text_bytes(data) - mission_text_bytes(src),
                    'Mission container carries dead bytes: ' + loc)
            checked['mission tables'] += 1
        elif parts and parts[-1].startswith(':s'):
            sid = int(parts[-1][2:])
            got = next(t.rows for s, off, t in small_tables(data) if s == sid)
            src = locate(disc.get(rid), parts)
            # containers without a dialogue table (6036, 6330...) have only this check
            require(len(data) - len(src) == mission_text_bytes(data) - mission_text_bytes(src),
                    'Mission container carries dead bytes: ' + loc)
            checked['unit-name sub-tables'] += 1
        elif parts and parts[-1].startswith(':v'):
            magic = parts[-1][2:].encode().ljust(4, b'\0')
            at, _, size = next(c for c in vmd_chunks(data) if c[1] == magic)
            got = TextTable(data[at + 16:at + size]).rows
            checked['partner package tables'] += 1
        else:
            got = TextTable(data).rows
            checked['tables'] += 1
        require(got == expect, 'Rows differ at ' + loc)
    summary = plan(BASE, new, {})
    print('PASS %s; %d resources rebuilt; DATA.BIN %d -> %d (+%d), tail left %d bytes'
          % (dict(checked), len(new), summary['data_bin'][0], summary['data_bin'][1],
             summary['data_bin'][1] - summary['data_bin'][0], summary['tail_left_bytes']))


if __name__ == '__main__':
    main()
