"""Text discovery shared by export, validation and build.

Every text table on the base disc is found by walking DATA.BIN (inner binders and LZSS-packed payloads are opened
recursively). A location is a path string:
  '6012:m'            dialogue table of mission container 6012 (pointer at +20)
  '6012:s219'         enemy-name sub-table 219 of mission container 6012
  '62050/3004'        text table 3004 inside inner binder 62050
  '1234:lz/5'         entry 5 of the binder packed inside resource 1234
  '2070:vPMS'         text table of chunk PMS of the VMD model package 2070 (partner chatter; also vPPN1, vPPN2)
Locations are grouped into logical tables (one JSON file each); rows are keyed by the Japanese source, so one
translation reaches every copy and every slot that carries the same text.
"""
import re, struct
from ace2lib import u32, align, Disc, inner_entries, inner_rebuild, try_unpack, pack, unpack, TextTable, mission_table, \
    mission_container, mission_relayout, list_a, small_tables, require, vmd_chunks, vmd_replace, VMD_TEXT

JPC = re.compile(r'[぀-ヿ一-鿿]')
# control tokens that must survive translation in the same order
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>|#c\[[0-9A-Fa-f]{6}\]|#c|#i|%[-0-9]*[ds]|%%|[○×△□①-⑳㈠-㏿]')
MAX_SCAN = 64 << 20


def _walk(data, path, depth, out):
    if mission_container(data):
        mt = mission_table(data)
        if mt:
            out.append((path + ':m', mt[1]))
        for sid, off, t in small_tables(data):
            out.append(('%s:s%d' % (path, sid), t))
        return
    if data[:4] == b'\0\0\1\0':
        try:
            out.append((path, TextTable(data)))
            return
        except (ValueError, UnicodeError):
            pass
    chunks = vmd_chunks(data)
    if chunks:
        for at, magic, size in chunks:
            if magic in VMD_TEXT:
                out.append(('%s:v%s' % (path, magic.rstrip(b'\0').decode()), TextTable(data[at + 16:at + size])))
        return
    plain = try_unpack(data) if depth < 4 else None
    if plain is not None:
        _walk(plain, path + ':lz', depth + 1, out)
        return
    rows = inner_entries(data)
    if rows and depth < 4:
        for e, a, b in rows:
            _walk(data[a:b], '%s/%d' % (path, e), depth + 1, out)


def discover(disc):
    """[(location, TextTable)] for every text table on the disc."""
    out = []
    for rid in disc.ids():
        if disc.index.by_id[rid][2] <= MAX_SCAN:
            _walk(disc.get(rid), str(rid), 0, out)
    return out


def family(location):
    """Logical table name of one location (before identical-content merging)."""
    top = int(re.match(r'\d+', location).group())
    if location.endswith(':vPMS'):
        # partner package pNNN is resource 2NNN, and 36300+NNN packed
        return 'partner%03d' % (top - 36300 if top >= 36000 else top - 2000)
    if ':vPPN' in location:
        return 'partner_names'
    if ':s' in location:
        return 'unit_names'
    if location.endswith(':m'):
        return 'm%04d' % (top - 36000 if top >= 42000 else top)
    inner = location.split('/')[-1] if '/' in location else None
    if 62000 <= top < 63000:
        return 'menu%s' % inner
    if 38000 <= top < 39000:
        return 'hud%s' % inner
    if 63000 <= top < 64000:
        return 'brief%d' % top
    if top in (8031, 8033, 60000):
        return 'common'
    return 'r%s' % location.replace('/', '_').replace(':', '_')


def group(found):
    """{name: [(location, TextTable)]}. A location without a family of its own ('r...') joins the named table whose rows
    are identical (e.g. encyclopedia 5000/2 == menu 3077), so the same text is translated once."""
    names, by_content, loose = {}, {}, []
    for loc, t in found:
        name = family(loc)
        if name.startswith('r'):
            loose.append((name, loc, t)); continue
        by_content.setdefault(tuple(sorted(t.rows.items())), name)
        names.setdefault(name, []).append((loc, t))
    for name, loc, t in loose:
        name = by_content.get(tuple(sorted(t.rows.items())), name)
        names.setdefault(name, []).append((loc, t))
    return names


# ---------------------------------------------------------------- writing back

def _split(location):
    """'62050/3004' -> (62050, ['3004']); '6012:m' -> (6012, [':m']); '1:lz/5' -> (1, [':lz', '5'])."""
    m = re.match(r'(\d+)(.*)$', location)
    rest, parts = m.group(2), []
    for token in re.findall(r':lz|:m|:s\d+|:v[A-Z0-9]+|/\d+', rest):
        parts.append(token.lstrip('/'))
    return int(m.group(1)), parts


def apply(data, parts, fn):
    """Rebuild data with fn applied to the payload at the nested path (parts from _split, ':m'/':s' excluded)."""
    if not parts:
        return fn(data)
    head, rest = parts[0], parts[1:]
    if head == ':lz':
        return pack(apply(unpack(data), rest, fn))
    if head.startswith(':v'):
        return vmd_replace(data, head[2:].encode().ljust(4, b'\0'), lambda table: apply(table, rest, fn))
    eid = int(head)
    sub = next(data[a:b] for e, a, b in inner_entries(data) if e == eid)
    return inner_rebuild(data, {eid: apply(sub, rest, fn)})


def rebuild_table(data, texts):
    """Table bytes with every row whose Japanese source has a translation replaced (unchanged bytes otherwise)."""
    t = TextTable(data)
    rows = {tid: texts[jp] for tid, jp in t.rows.items() if jp in texts}
    return t.rebuild(rows) if rows else data


def patch_mission(container, sub_texts, main_texts):
    """Mission container with translated sub-tables and dialogue table. Nothing is squeezed: each table is rebuilt at
    its full new size where the Japanese one was, and the sections after it move (ace2lib.mission_relayout). Appending
    the tables instead (ACE3 method) leaves the Japanese ones as dead weight in the game's memory arena, which made
    Op 12-1 run out of memory after its cutscene (0.0.10). Bytes that are not text stay identical."""
    replace = {}
    for sid, off in list_a(container):
        if sid not in sub_texts or off in replace:
            continue
        try:
            t = TextTable(container[off:])
        except (ValueError, UnicodeError, struct.error):
            continue
        new = rebuild_table(container[off:off + t.size], sub_texts[sid])
        if new != container[off:off + t.size]:
            replace[off] = new
    mt = mission_table(container)
    if mt:
        at, t = mt
        rows = {tid: main_texts[jp] for tid, jp in t.rows.items() if jp in main_texts}
        if rows:
            replace[at] = t.rebuild(rows)
    return mission_relayout(container, replace) if replace else container


def patch_resource(data, locations, texts_for):
    """Apply every location of one top-level resource. texts_for(location) -> {jp: en} (may be empty)."""
    missions = {}
    for loc in locations:
        rid, parts = _split(loc)
        if parts and parts[-1].startswith(':s'):
            missions.setdefault(tuple(parts[:-1]), [{}, {}])[0][int(parts[-1][2:])] = texts_for(loc)
        elif parts and parts[-1] == ':m':
            missions.setdefault(tuple(parts[:-1]), [{}, {}])[1] = texts_for(loc)
        else:
            texts = texts_for(loc)
            if texts:
                data = apply(data, parts, lambda table, texts=texts: rebuild_table(table, texts))
    for prefix, (subs, main) in missions.items():
        subs = {k: v for k, v in subs.items() if v}
        if subs or main:
            data = apply(data, list(prefix), lambda c, subs=subs, main=main: patch_mission(c, subs, main))
    return data
