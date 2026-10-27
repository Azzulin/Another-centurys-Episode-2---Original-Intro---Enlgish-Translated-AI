"""Independent audit of a built image against the base disc (reads the output only; writes nothing).

  python tools/ace2/audit_iso.py <image.iso>
  python tools/ace2/audit_iso.py <image.iso> --svv-opening     image built with build.py --svv-opening

Checks:
  layout    DATA.BIN entries ascending, 2048-aligned, non-overlapping, inside DATA.BIN; ISO9660 extents non-overlapping
  files     every file other than DATA.BIN, MOVIE001.PSS and SLPS_258.29 byte-identical to the base; MOVIE001.PSS
            identical to the original 2006 release (opening with "Glorious"), or to the base with --svv-opening;
            SLPS_258.29 equal to the base with the exe.py patches and nothing else (stack/heap boundary, message
            window capacity)
  text      every text location of the base disc still parses (no pointer or string outside its table) and every
            row keeps the control tokens of its Japanese source in the same order
  rest      every DATA.BIN resource that has no text and no font is byte-identical to the base
  memory    every mission container grows exactly by the growth of its text tables: no dead Japanese table left
            behind (the game loads the container whole into a memory arena with no room to spare; Op 12-1 froze in
            0.0.10 when containers carried their old tables). Prints the largest growth.
"""
import collections, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ace2lib import BASE, BASE_EXE, ORIGINAL_RELEASE, SECTOR, Disc, iso_files, mission_container, mission_text_bytes, \
    require
import exe
from textdb import discover, TOKEN
from disc import file_digest

MOVIE = '/MOVIE0/MOVIE001.PSS'


def main():
    image = Path(sys.argv[1])
    out, base = Disc(image), Disc(BASE)
    movie_disc = BASE if '--svv-opening' in sys.argv[2:] else ORIGINAL_RELEASE
    problems = collections.Counter(); samples = collections.defaultdict(list)

    def bad(kind, detail):
        problems[kind] += 1
        if len(samples[kind]) < 8:
            samples[kind].append(detail)

    # layout
    ents = sorted(out.index.entries, key=lambda e: e[1])
    for a, b in zip(ents, ents[1:]):
        if a[1] + a[2] > b[1]:
            bad('overlapping resources', '%d@%d+%d overlaps %d@%d' % (a[0], a[1], a[2], b[0], b[1]))
    for e in ents:
        if e[1] % SECTOR or e[1] + e[2] > out.data_file['size']:
            bad('resource outside DATA.BIN or unaligned', str(e))
    ext = sorted(out.files.values(), key=lambda v: v['offset'])
    for a, b in zip(ext, ext[1:]):
        if a['offset'] + a['size'] > b['offset']:
            bad('overlapping files', str((a, b)))
    # files
    with movie_disc.open('rb') as orig:
        movie = iso_files(orig)[MOVIE]
        want_movie = file_digest(orig, movie['offset'], movie['size'])
    for name, rec in out.files.items():
        if name == '/DATA.BIN':
            continue
        got = file_digest(out.stream, rec['offset'], rec['size'])
        if name == MOVIE:
            if got != want_movie:
                bad('MOVIE001 is not the expected opening', name)
        elif name == BASE_EXE:
            if exe.read_exe(out) != exe.patch(exe.read_exe(base)):
                bad('executable differs from base + exe.py patches', name)
        elif got != file_digest(base.stream, base.files[name]['offset'], base.files[name]['size']):
            bad('file changed', name)
    # text
    before = dict(discover(base))
    after = dict(discover(out))
    touched = set()
    for loc, t in before.items():
        if loc not in after:
            bad('text table broken', loc); continue
        rows = after[loc].rows
        if rows != t.rows:
            touched.add(int(loc.split('/')[0].split(':')[0]))
        for tid, jp in t.rows.items():
            en = rows.get(tid)
            if en is None:
                bad('row lost', '%s/%d' % (loc, tid))
            elif TOKEN.findall(jp) != TOKEN.findall(en):
                bad('control tokens changed', '%s/%d: %r -> %r' % (loc, tid, jp[:40], en[:40]))
    # untouched resources
    fonts = set(range(38000, 38007)) | set(range(62050, 62058))
    changed = [rid for rid in base.ids() if base.index.by_id[rid][2] != out.index.by_id[rid][2] or base.get(rid) != out.get(rid)]
    for rid in changed:
        if rid not in touched and rid not in fonts:
            bad('resource changed without text/font reason', str(rid))
    # memory
    growth, partner = {}, {}
    for rid in changed:
        old, new = base.get(rid), out.get(rid)
        if 2000 <= rid < 2300 and old[:4] == b'VMD\0':
            partner[rid] = len(new) - len(old)
        if mission_container(old) and mission_container(new):
            growth[rid] = len(new) - len(old)
            if growth[rid] != mission_text_bytes(new) - mission_text_bytes(old):
                bad('mission container carries dead bytes', '%d: +%d bytes, text tables +%d'
                    % (rid, growth[rid], mission_text_bytes(new) - mission_text_bytes(old)))
    print('image', image.name, '| resources changed:', len(changed), '| text locations:', len(before))
    if growth:
        top = max(growth, key=growth.get)
        print('mission containers: %d rebuilt, largest growth %+d bytes (%d), total %+d bytes'
              % (len(growth), growth[top], top, sum(growth.values())))
    if partner:
        top = max(partner, key=partner.get)
        print('partner packages (resident in missions): %d rebuilt, largest growth %+d bytes (%d)' % (len(partner), partner[top], top))
    if not problems:
        print('PASS: layout, files, opening movie, text integrity, control tokens and mission memory')
        return
    for kind, n in problems.most_common():
        print('FAIL %-45s %d' % (kind, n))
        for s in samples[kind]:
            print('      ', s)
    raise SystemExit(1)


if __name__ == '__main__':
    main()
