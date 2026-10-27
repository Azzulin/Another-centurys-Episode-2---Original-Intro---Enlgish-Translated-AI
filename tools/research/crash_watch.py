"""Watch ACE2 running in PCSX2 (PINE interface) to find what a freeze overwrites. Reads the game; never writes to it.

  python tools/research/crash_watch.py watch [--iso ISO] [--port 28011] [--slot 10] [--interval 0.5]
  python tools/research/crash_watch.py check <ram.bin | savestate.p2s> [--iso ISO]

PCSX2 (2.x): Settings > Advanced > "Enable PINE" (slot 28011). Optional: Tools > Show Advanced Settings, then
Settings > Advanced > Logging > "EE Console", so the game's own debug prints go to logs/emulog.txt.

watch
  - polls the game's memory arena (allocator of SLPS_258.29 at 0x345040) about 50 times a second and logs the free
    space, its lows, the top block and the scene levels; when less than 16 KB is left (requests start returning
    NULL: the Op 12-1 freeze of 0.0.10, ESTUDO 8.6) it saves a savestate and a RAM dump;
  - logs every resource the game loads (its own list: id, address, size);
  - every 3 s, lists the text widgets in RAM (capacity, characters, text) and dumps the moment one writes more
    than its buffer holds (texts longer than the widget's capacity: the Op 12-1 freeze, tools/ace2/exe.py);
  - finds in EE RAM every translated mission container of the ISO (anchor: its English dialogue table; also the
    Japanese one in builds up to 0.0.10, which appended the English table) and compares it with the ISO in 1 KB
    pages, per section: header and tables / dialogue table / unit images / +32 section;
  - polls the containers it found and logs every change of their bytes, with the section and the time;
  - the first time a page of the dialogue table stops matching the ISO, or a container leaves memory, it saves a
    savestate (PINE, slot --slot: that slot is overwritten) and a 32 MB RAM dump;
  - console: a typed line is a note in the log; 'd' = savestate + RAM dump now (use it when the game freezes);
    'r' = rescan RAM; 'q' = quit.
  Output: work/crash/<date-time>/ (log.txt, ram_N.bin, the savestates, a copy of emulog.txt).
check
  the same search and comparison on a RAM dump or a savestate, plus the EE registers (pc, ra, sp) and the code
  addresses found on the stack, when the input is a savestate.
"""
import argparse, datetime, io, queue, re, shutil, socket, struct, sys, threading, time, zipfile
from array import array
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ace2'))
from ace2lib import ROOT, BASE, Disc, TextTable, mission_table, is_packed, u32

OUT = ROOT / 'work' / 'crash'
RAM_SIZE = 32 << 20
PAGE = 1024
CODE = (0x100000, 0x327e80)          # .text of SLPS_258.29
PCSX2_DIRS = [Path.home() / 'Downloads' / 'PCSX2', Path('C:/PCSX2'), Path.home() / 'Documents' / 'PCSX2']


def say(*parts):
    print(*parts, flush=True)


# ---------------------------------------------------------------- PINE client

class PineError(Exception):
    pass


class Pine:
    READ64, VERSION, SAVE, TITLE, ID, STATUS = 3, 8, 9, 0xB, 0xC, 0xF
    BATCH = 40000                    # reads per message (PCSX2 replies hold up to 450000 bytes)

    def __init__(self, port):
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=30)

    def _recv(self, n):
        out = bytearray()
        while len(out) < n:
            chunk = self.sock.recv(n - len(out))
            if not chunk:
                raise PineError('PCSX2 closed the connection')
            out += chunk
        return bytes(out)

    def call(self, body):
        self.sock.sendall(struct.pack('<I', len(body) + 4) + body)
        size = struct.unpack('<I', self._recv(4))[0]
        reply = self._recv(size - 4)
        if reply[:1] != b'\0':
            raise PineError('PINE refused the request (no game running?)')
        return reply[1:]

    def text(self, op):
        r = self.call(bytes([op]))
        return r[4:4 + u32(r, 0)].split(b'\0')[0].decode('utf-8', 'replace')

    def status(self):
        return {0: 'rodando', 1: 'pausado', 2: 'desligado'}.get(u32(self.call(bytes([self.STATUS])), 0), '?')

    def read(self, addr, size):
        start, end = addr & ~7, (addr + size + 7) & ~7
        out = bytearray()
        for at in range(start, end, self.BATCH * 8):
            n = min(self.BATCH, (end - at) // 8)
            addrs = array('I', range(at, at + n * 8, 8)).tobytes()
            body = bytearray(5 * n)
            body[0::5] = bytes([self.READ64]) * n
            for k in range(4):
                body[1 + k::5] = addrs[k::4]
            out += self.call(bytes(body))
        return bytes(out[addr - start:addr - start + size])

    def save_state(self, slot):
        self.call(bytes([self.SAVE, slot]))


# ---------------------------------------------------------------- containers of the ISO

def peek(disc, rid, n):
    _, off, size = disc.index.by_id[rid]
    disc.stream.seek(disc.data_file['offset'] + off)
    return disc.stream.read(min(n, size)), size


def pool_offset(table_bytes):
    """Offset (inside the table) of its first string."""
    t = TextTable(table_bytes)
    return min(u32(t.data, t.pointers + 4 * i) for i in range(len(t.ids)) if u32(t.data, t.pointers + 4 * i))


DIALOGUE = 'TABELA DE DIALOGO'


def sections(new):
    """[(name, start, end)] of a built mission container, read from its own header. Builds up to 0.0.10 appended the
    English table after the last section; from 0.0.11 it sits where the Japanese one was (ace2lib.mission_relayout)."""
    h = struct.unpack_from('<9I', new)
    images = []
    if new[31] and 0 < h[1] < len(new):
        for i in range(new[31]):
            at = h[1] + i * 16 + 8
            if at + 4 <= len(new) and 0 < u32(new, at) < len(new):
                images.append(u32(new, at))
    at20 = h[5]
    t_end = at20 + TextTable(new[at20:]).size
    resident = min(images) if images else len(new)
    out = []
    if at20 < resident:
        out += [('cabecalho+tabelas', 0, at20), (DIALOGUE, at20, t_end), ('cabecalho+tabelas', t_end, resident)]
    else:
        out.append(('cabecalho+tabelas', 0, resident))
    if images:
        last = h[8] if h[2] == 0x30 and resident <= h[8] < len(new) else None
        out.append(('imagens', resident, last or (at20 if at20 >= resident else len(new))))
        if last:
            out.append(('secao+32', last, at20 if at20 > last else len(new)))
    if at20 >= resident:
        out.append((DIALOGUE + ' (anexada no fim)', at20, len(new)))
    return out


def catalog(iso):
    """Translated mission containers of the ISO: rid, bytes, sections and the anchors that locate them in RAM."""
    base, test = Disc(BASE), Disc(iso)
    out = []
    for rid in test.ids():
        head, size = peek(test, rid, 12)
        if head[:4] != b'\0\1\0\0' or is_packed(head, size) or size > 4 << 20 or rid not in base.index.by_id:
            continue
        old, new = base.get(rid), test.get(rid)
        mt = mission_table(old)
        if old == new or not mt:
            continue
        at20 = u32(new, 20)
        at = at20 + pool_offset(new[at20:])
        anchors = [('tabela EN', new[at:at + 64], at)]
        at = mt[0] + pool_offset(old[mt[0]:])
        if new[at:at + 64] == old[at:at + 64]:                          # Japanese table left in place (<= 0.0.10)
            anchors.append(('tabela JP', new[at:at + 64], at))
        out.append({'rid': rid, 'new': new, 'old_len': len(old), 'sections': sections(new), 'anchors': anchors})
    base.close(); test.close()
    return out


def section_of(entry, off):
    return next((name for name, a, b in entry['sections'] if a <= off < b), 'depois do fim')


def pages_equal(ram, base, new):
    return [ram[base + p:base + min(p + PAGE, len(new))] == new[p:p + PAGE] for p in range(0, len(new), PAGE)]


def locate(ram, cat):
    """[(score, entry, base)] for every container copy found in a RAM image (best container per base address).
    A container is loaded word-aligned, so each anchor is looked up by one of its aligned 32-bit words (numpy), then
    checked in full."""
    import numpy as np
    keys = {}
    for entry in cat:
        for _, anchor, off in entry['anchors']:
            spots = range((off + 3) & ~3, off + len(anchor) - 3, 4)
            w = next((w for w in spots if b'\0' not in entry['new'][w:w + 4]), spots[0])
            keys.setdefault(u32(entry['new'], w), []).append((entry, anchor, off, w))
    words = np.frombuffer(ram, dtype='<u4', count=len(ram) // 4)
    best = {}
    for idx in np.nonzero(np.isin(words, np.array(list(keys), dtype='<u4')))[0]:
        for entry, anchor, off, w in keys[int(words[idx])]:
            b = int(idx) * 4 - w
            if b < 0 or (b, entry['rid']) in best or ram[b + off:b + off + len(anchor)] != anchor:
                continue
            eq = pages_equal(ram, b, entry['new'])
            best[(b, entry['rid'])] = (sum(eq) / len(eq), entry, b)
    by_base = {}
    for score, entry, b in best.values():
        if score >= by_base.get(b, (0,))[0]:
            by_base[b] = (score, entry, b)
    return sorted((x for x in by_base.values() if x[0] >= 0.25), key=lambda x: x[2])


def ranges(offsets):
    """[a, b, c...] page offsets -> '0x..-0x.., ...'"""
    out, start, prev = [], None, None
    for o in offsets:
        if start is None:
            start = prev = o
        elif o == prev + PAGE:
            prev = o
        else:
            out.append((start, prev)); start = prev = o
    if start is not None:
        out.append((start, prev))
    return ', '.join('+0x%x' % a if a == b else '+0x%x..+0x%x' % (a, b + PAGE) for a, b in out[:12]) + \
        (' ...' if len(out) > 12 else '')


def report(ram, entry, b):
    """Per-section comparison of one container copy with the ISO, and the dialogue table its +20 points to."""
    new = entry['new']
    eq = pages_equal(ram, b, new)
    lines = ['%d @ 0x%08x  (%d bytes; %.0f%% das paginas iguais a ISO)' % (entry['rid'], b, len(new), 100 * sum(eq) / len(eq))]
    for name, s, e in entry['sections']:
        idx = range(s // PAGE, min((e + PAGE - 1) // PAGE, len(eq)))
        bad = [p * PAGE for p in idx if not eq[p]]
        lines.append('  %-26s +0x%06x..+0x%06x  %4d/%-4d iguais%s' % (
            name, s, e, len(idx) - len(bad), len(idx), ('   diferem: ' + ranges(bad)) if bad else ''))
    p20 = u32(ram, b + 20)
    target = p20 if 0x100000 <= p20 < RAM_SIZE else b + p20
    try:
        t = TextTable(ram[target:target + 0x40000])
        state = 'tabela valida, %d linhas' % len(t.rows)
    except Exception as ex:
        state = 'TABELA INVALIDA (%s)' % ex
    lines.append('  +20 na RAM = 0x%x (ISO 0x%x) -> 0x%08x: %s' % (p20, u32(new, 20), target, state))
    return lines


# ---------------------------------------------------------------- savestates (PCSX2 2.x .p2s = zip)

def zip_member(path, name):
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(name)
        try:
            return z.read(name)
        except NotImplementedError:
            pass
        with open(path, 'rb') as f:
            f.seek(info.header_offset)
            local = f.read(30)
            f.seek(info.header_offset + 30 + struct.unpack_from('<H', local, 26)[0] + struct.unpack_from('<H', local, 28)[0])
            raw = f.read(info.compress_size)
    if info.compress_type != 93:
        raise SystemExit('%s: compressao zip %d nao suportada' % (name, info.compress_type))
    try:
        from compression import zstd                       # Python 3.14
        return zstd.decompress(raw)
    except ImportError:
        pass
    try:
        import zstandard
    except ImportError:
        raise SystemExit('Savestate em zstd: instale o pacote zstandard (pip install zstandard) ou use Python 3.14.')
    return zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)).read()


def registers(state):
    """EE registers from 'PCSX2 Internal Structures.dat': cpuRegs follows the 32-byte tag 'cpuRegs'."""
    at = state.find(b'cpuRegs\0')
    if at < 0:
        return None
    r = at + 32
    gpr = lambda n: u32(state, r + n * 16)
    regs = {'pc': u32(state, r + 680), 'ra': gpr(31), 'sp': gpr(29), 'v0': gpr(2), 'v1': gpr(3), 'a0': gpr(4),
            'a1': gpr(5), 'a2': gpr(6), 'a3': gpr(7), 's0': gpr(16), 's1': gpr(17), 's2': gpr(18), 'gp': gpr(28)}
    return regs if (CODE[0] <= regs['pc'] < 0x2000000 or regs['pc'] >= 0x80000000) else None


def load_image(path):
    """(ram, regs or None) from a raw 32 MB dump or a savestate."""
    path = Path(path)
    if path.suffix.lower() != '.p2s':
        return path.read_bytes(), None
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    ram = zip_member(path, next(n for n in names if n.lower().startswith('eememory')))
    internal = next((n for n in names if 'internal' in n.lower()), None)
    return ram, (registers(zip_member(path, internal)) if internal else None)


def stack_codes(ram, sp, n=24):
    """Words on the stack that look like return addresses into the game code (call chain hint)."""
    out = []
    for at in range(sp & 0x1fffffc, min((sp & 0x1fffffc) + 0x2000, RAM_SIZE), 4):
        w = u32(ram, at)
        if CODE[0] <= w < CODE[1] and w % 4 == 0 and u32(ram, w - 8) >> 26 == 3:      # word before is a jal
            out.append('sp+0x%x: 0x%x' % (at - (sp & 0x1fffffc), w))
            if len(out) == n:
                break
    return out


def analyse(ram, regs, cat):
    lines = []
    if regs:
        lines.append('Registradores EE: ' + '  '.join('%s=0x%08x' % kv for kv in regs.items()))
        pc = regs['pc'] & 0x1ffffff
        if pc + 16 <= len(ram):
            lines.append('  palavras em pc: ' + ram[pc:pc + 16].hex(' ', 4))
        lines.append('  pilha (enderecos de retorno): ' + '; '.join(stack_codes(ram, regs['sp'])))
    lines.append('Arena: ' + Arena(ram[ARENA:ARENA + 0x80]).describe())
    table = Arena.load_table(ram)
    if table:
        recs = [r for r in Arena.records(ram[table[0]:table[1]]) if r]
        lines.append('Recursos carregados (lista em %08x): ' % table[0] +
                     '; '.join('%d @ %08x+%d' % r for r in sorted(set(recs), key=lambda r: r[1])))
    widgets = text_widgets(ram)
    lines.append('Textos na tela/memoria: %d widgets' % len(widgets))
    for obj, cap, glyphs, used, size, text in widgets:
        lines.append('  %s %08x capacidade %3d, usa %3d qw de %3d: %r' % (
            'TRANSBORDA' if used * 16 > size else 'ok        ', obj, cap, used, size // 16, text[:90]))
    found = locate(ram, cat)
    if not found:
        lines.append('Nenhum contêiner de missão traduzido encontrado na RAM.')
    for score, entry, b in found:
        lines.extend(report(ram, entry, b))
    return lines


# ---------------------------------------------------------------- the game's memory arena

ARENA = 0x345040        # SLPS_258.29 allocator 0x14ff80: (capacity, base, cursor, top block) x2, marks, saved levels
MARKS, LEVELS, LEVEL = 0x345084, 0x345060, 0x3450b0
STACK = 0x01f40000      # main thread stack bottom from 0.0.12 (0x01f00000 before; tools/ace2/exe.py)


class Arena:
    """One snapshot of arena 0. Allocations go up from the cursor; one block at a time can be taken from the top
    (capacity shrinks by it); marks (levels 0-7) let a scene free everything allocated after it in one go. A request
    that does not fit returns NULL, and the game does not check it."""

    def __init__(self, raw):
        self.capacity, self.base, self.cursor, self.top = struct.unpack_from('<4I', raw, 0)
        self.marks = struct.unpack_from('<8I', raw, MARKS - ARENA)
        self.level = struct.unpack_from('<i', raw, LEVEL - ARENA)[0]
        self.free = self.capacity - (self.cursor - self.base)

    @staticmethod
    def read(pine):
        return Arena(pine.read(ARENA, 0x80))

    def shape(self):
        return (self.top, self.level, self.marks)

    @staticmethod
    def load_table(ram):
        """(start, end) of the game's list of loaded resources (id, address, size, 0), groups separated by -1/-2:
        the longest run of such 16-byte records in the heap just above the executable."""
        best, start = (0, 0), None
        for at in range(0x00380000, 0x00400000, 16):
            rid, addr, size, _ = struct.unpack_from('<4I', ram, at)
            ok = (rid in (0xffffffff, 0xfffffffe) and addr == size == 0) or \
                 ((rid < 100000 or rid == 0x7fffffff) and 0x100000 <= addr < RAM_SIZE and 0 < size < RAM_SIZE)
            if ok and start is None:
                start = at
            elif not ok and start is not None:
                if at - start > best[1] - best[0]:
                    best = (start, at)
                start = None
        return best if best[1] - best[0] >= 16 * 16 else None

    @staticmethod
    def records(raw):
        out = []
        for i in range(0, len(raw) - 15, 16):
            rid, addr, size, _ = struct.unpack_from('<4I', raw, i)
            out.append((rid, addr, size) if 0x100000 <= addr < RAM_SIZE and size else None)
        return out

    def describe(self):
        marks = ' '.join('%d:%08x' % (i, m) for i, m in enumerate(self.marks) if m)
        return ('livre %7.1f KB | cursor %08x | bloco do topo %6.0f KB (de %08x) | nivel %d | marcas %s'
                % (self.free / 1024, self.cursor, self.top / 1024, self.base + self.capacity, self.level, marks))


# ---------------------------------------------------------------- text widgets

# buffer bytes of a text widget of capacity n -> [(n, quadwords per character, fixed quadwords)], for both classes:
# allocator 0x289e30 reserves (7 n + 11) * 16 (0x1a18e0), allocator 0x28a0f0 (11 n + 12) * 16 + 32 (0x1a0f80; the
# victory/defeat conditions and help lines of the pause menu). Capacity 32 unless the owner sets another (init 0x289dfc).
SIZE_OF = {}
for _n in range(1, 256):
    SIZE_OF.setdefault((7 * _n + 11) * 16, []).append((_n, 7, 11))
    SIZE_OF.setdefault((11 * _n + 12) * 16 + 32, []).append((_n, 11, 12))


def text_widgets(ram):
    """Text widgets in RAM (class with init 0x289bd0): one sprite per character, buffer reserved once from the
    capacity; the game never checks it (tools/ace2/exe.py, validate.py). Object: +0x88 quadwords used, +0x8c buffer
    bytes, +0x90 buffer, +0x98 descriptor (+0x1b capacity, +0x1c text). [(object, capacity, glyphs, used, bytes, text)]"""
    import numpy as np
    w = np.frombuffer(ram, dtype='<u4', count=len(ram) // 4)
    out = []
    for i in np.nonzero(np.isin(w, np.array(list(SIZE_OF), dtype='<u4')))[0]:
        i = int(i)
        if i < 1 or i + 3 >= len(w):
            continue
        size, buf, desc = int(w[i]), int(w[i + 1]), int(w[i + 3])
        if not (0x100000 <= buf < RAM_SIZE and 0x100000 <= desc < RAM_SIZE - 0x20):
            continue
        shape = [s for s in SIZE_OF[size] if s[0] == ram[desc + 0x1b]]
        if not shape:
            continue
        cap, per, base = shape[0]
        used = int(w[i - 1])
        ptr = u32(ram, desc + 0x1c)
        text = ram[ptr:ptr + 300].split(b'\0')[0].decode('cp932', 'replace') if 0x100000 <= ptr < RAM_SIZE else ''
        out.append((i * 4 - 0x8c, cap, (used - base) // per if used >= base else 0, used, size, text))
    return out


def overflowing(widgets):
    return [x for x in widgets if x[3] * 16 > x[4]]


# ---------------------------------------------------------------- watch

class Watch:
    def __init__(self, args):
        self.args = args
        self.dir = OUT / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.dir.mkdir(parents=True)
        self.logf = (self.dir / 'log.txt').open('a', encoding='utf-8')
        self.dumps = 0
        self.tracked = []
        self.commands = queue.Queue()
        self.arena = None            # last snapshot
        self.low = None              # lowest free space seen, and since the last change of shape
        self.phase_low = None
        self.arena_dump_at = 0
        self.table = None            # (start, end) of the load list, and its last records
        self.table_rows = []
        self.stack_used = 0
        self.texts_seen = set()

    def log(self, *lines):
        stamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        for line in lines:
            say('[%s] %s' % (stamp, line))
            self.logf.write('[%s] %s\n' % (stamp, line))
        self.logf.flush()

    def stdin(self):
        for line in sys.stdin:
            self.commands.put(line.strip())

    def scan(self):
        t = time.time()
        ram = self.pine.read(0, RAM_SIZE)
        found = locate(ram, self.cat)
        self.tracked = []
        for score, entry, b in found:
            self.log(*report(ram, entry, b))
            data = ram[b:b + len(entry['new'])]
            self.tracked.append({'entry': entry, 'base': b, 'prev': data, 'iso': pages_equal(ram, b, entry['new']),
                                 'alerted': False, 'last': None, 'repeat': 0})
        self.log('Varredura da RAM em %.1fs: %d contêiner(es) de missão traduzido(s) na memória.' % (time.time() - t, len(found)))
        table = Arena.load_table(ram)
        if table and table != self.table:
            self.table = table
            self.table_rows = Arena.records(ram[table[0]:table[1] + 0x400])
            self.log('Lista de recursos carregados em %08x..%08x' % table)
        return ram

    def watch_arena(self):
        """Fast poll of the allocator: logs every change of the top block / level / marks, every new low of the free
        space, and dumps (savestate + RAM) when the arena is almost full, the condition that froze Op 12-1."""
        a = Arena.read(self.pine)
        if self.arena is None or a.shape() != self.arena.shape():
            if self.arena is not None and self.phase_low is not None:
                self.log('arena: minimo nesta etapa %.1f KB' % (self.phase_low / 1024))
            self.log('arena: ' + a.describe())
            self.phase_low = a.free
        self.phase_low = min(self.phase_low, a.free)
        if self.low is None or a.free < self.low - 16384:
            self.low = a.free
            self.log('arena: novo minimo -> ' + a.describe())
        if a.free < 16384 and time.time() - self.arena_dump_at > 60 and self.dumps < 6:
            self.arena_dump_at = time.time()
            self.log('ALERTA: arena quase cheia (%.1f KB livres): alocacoes do jogo podem voltar NULL' % (a.free / 1024))
            self.dump('arena quase cheia')
        self.arena = a

    def watch_stack(self):
        """Deepest stack use since boot (the stack is never cleared): from 0.0.12 it has 768 KB (tools/ace2/exe.py)."""
        st = self.pine.read(STACK, 0x02000000 - STACK)
        first = next((i for i in range(0, len(st), 4) if st[i:i + 4] != b'\0\0\0\0'), len(st))
        used = len(st) - first
        if used > self.stack_used + 8192:
            self.stack_used = used
            self.log('pilha: uso maximo desde o boot %d KB de %d KB' % (used // 1024, len(st) // 1024))
            if used > 600 * 1024:
                self.log('ALERTA: pilha acima de 600 KB')

    def watch_texts(self):
        """Every text widget in RAM: logs each new text with its capacity, and dumps the moment one uses more of its
        buffer than it reserved (the overflow that froze Op 12-1)."""
        for obj, cap, glyphs, used, size, text in text_widgets(self.pine.read(0, RAM_SIZE)):
            key = (obj, text)
            if key in self.texts_seen or not text:
                continue
            self.texts_seen.add(key)
            over = used * 16 > size
            self.log('%s capacidade %3d, %3d letras: %r' % ('TEXTO TRANSBORDA!' if over else 'texto', cap, glyphs, text[:100]))
            if over and self.dumps < 6:
                self.log('ALERTA: o widget %08x escreveu %d bytes num buffer de %d' % (obj, used * 16, size))
                self.dump('texto maior que a capacidade do widget')

    def watch_table(self):
        a, b = self.table
        rows = Arena.records(self.pine.read(a, b - a + 0x400))
        for i, r in enumerate(rows):
            if r and (i >= len(self.table_rows) or self.table_rows[i] != r):
                self.log('carregado: recurso %d @ %08x..%08x (%d bytes)' % (r[0], r[1], r[1] + r[2], r[2]))
        self.table_rows = rows

    def dump(self, reason):
        self.dumps += 1
        n = self.dumps
        self.log('DUMP %d: %s' % (n, reason))
        t0 = time.time()
        try:
            self.pine.save_state(self.args.slot)
            self.log('  savestate pedido no slot %d' % self.args.slot)
        except PineError as ex:
            self.log('  savestate falhou: %s' % ex)
        ram = self.pine.read(0, RAM_SIZE)
        (self.dir / ('ram_%d.bin' % n)).write_bytes(ram)
        self.log('  RAM gravada: ram_%d.bin' % n)
        for line in analyse(ram, None, self.cat):
            self.log('  ' + line)
        deadline = time.time() + 15
        copied = False
        while time.time() < deadline and not copied:
            for d in self.args.pcsx2:
                for p in sorted((d / 'sstates').glob('*.p2s'), key=lambda p: p.stat().st_mtime, reverse=True)[:1]:
                    if p.stat().st_mtime >= t0 - 1:
                        time.sleep(1)
                        shutil.copy2(p, self.dir / ('state_%d_%s' % (n, p.name)))
                        self.log('  savestate copiado: state_%d_%s' % (n, p.name))
                        copied = True
            if not copied:
                time.sleep(0.5)
        if not copied:
            self.log('  savestate nao encontrado em %s' % ', '.join(str(d / 'sstates') for d in self.args.pcsx2))
        for d in self.args.pcsx2:
            if (d / 'logs' / 'emulog.txt').exists():
                shutil.copy2(d / 'logs' / 'emulog.txt', self.dir / ('emulog_%d.txt' % n))

    def tick(self):
        for tr in list(self.tracked):
            entry, b = tr['entry'], tr['base']
            new = entry['new']
            cur = self.pine.read(b, len(new))
            if cur == tr['prev']:
                continue
            changed, lost, back = [], [], []
            for i, p in enumerate(range(0, len(new), PAGE)):
                c = cur[p:p + PAGE]
                if c != tr['prev'][p:p + PAGE]:
                    changed.append(p)
                    iso = c == new[p:p + PAGE]
                    if tr['iso'][i] and not iso:
                        lost.append(p)
                    elif iso and not tr['iso'][i]:
                        back.append(p)
                    tr['iso'][i] = iso
            tr['prev'] = cur
            by_sec = {}
            for p in changed:
                by_sec.setdefault(section_of(entry, p), []).append(p)
            key = tuple((s, tuple(v)) for s, v in by_sec.items())
            if key == tr['last'] and not lost and not back:
                tr['repeat'] += 1
                if tr['repeat'] in (10, 100, 1000):
                    self.log('%d: a mesma mudanca repetiu %d vezes (dados de execucao do jogo)' % (entry['rid'], tr['repeat']))
                continue
            tr['last'], tr['repeat'] = key, 0
            self.log('%d @ 0x%08x mudou: %s' % (entry['rid'], b, '; '.join('%s %s' % (s, ranges(v)) for s, v in by_sec.items())))
            if lost:
                self.log('   deixaram de ser iguais a ISO: ' + ranges(lost))
            if back:
                self.log('   voltaram a ser iguais a ISO: ' + ranges(back))
            dialogue = [p for p in lost if section_of(entry, p).startswith(DIALOGUE)]
            score = sum(tr['iso']) / len(tr['iso'])
            if dialogue and not tr['alerted']:
                tr['alerted'] = True
                self.log('ALERTA: a tabela de dialogo do contêiner %d foi sobrescrita (%s)' % (entry['rid'], ranges(dialogue)))
                self.dump('tabela de dialogo do contêiner %d sobrescrita' % entry['rid'])
            if score < 0.25:
                self.log('%d saiu da memoria (so %.0f%% igual a ISO)' % (entry['rid'], 100 * score))
                if not tr['alerted']:
                    tr['alerted'] = True
                    self.dump('contêiner %d saiu da memoria' % entry['rid'])
                self.tracked.remove(tr)

    def run(self):
        self.log('Saida em %s' % self.dir)
        self.log('Lendo os contêineres de missão da ISO %s ...' % self.args.iso.name)
        self.cat = catalog(self.args.iso)
        self.log('%d contêineres traduzidos no catálogo.' % len(self.cat))
        self.log('Esperando o PCSX2 (porta %d; precisa de Configuracoes > Avancado > "Enable PINE") e o jogo...' % self.args.port)
        self.pine = None
        while True:
            try:
                self.pine = self.pine or Pine(self.args.port)
                self.log('PCSX2 %s | jogo %s (%s) | %s' % (self.pine.text(Pine.VERSION), self.pine.text(Pine.ID),
                                                           self.pine.text(Pine.TITLE), self.pine.status()))
                break
            except PineError:
                time.sleep(2)
            except OSError:
                self.pine = None
                time.sleep(2)
        self.log("Comandos: texto + Enter = nota no log; 'd' = savestate + dump da RAM agora (use quando travar); "
                 "'r' = varrer a RAM de novo; 'q' = sair.")
        threading.Thread(target=self.stdin, daemon=True).start()
        last_scan = next_tick = next_table = next_status = next_texts = 0
        while True:
            try:
                while not self.commands.empty():
                    cmd = self.commands.get()
                    if cmd == 'q':
                        self.log('arena: menor espaco livre visto %.1f KB' % ((self.low or 0) / 1024))
                        self.log('Fim.'); return
                    if cmd == 'd':
                        self.dump('pedido pelo usuario')
                    elif cmd == 'r':
                        self.scan(); last_scan = time.time()
                    elif cmd:
                        self.log('NOTA: ' + cmd + ' | arena ' + (self.arena.describe() if self.arena else '?'))
                self.watch_arena()
                now = time.time()
                if not self.tracked and now - last_scan > 10:
                    self.scan(); last_scan = time.time()
                if now >= next_tick:
                    self.tick(); next_tick = now + self.args.interval
                if self.table and now >= next_table:
                    self.watch_table(); next_table = now + 1
                if now >= next_texts:
                    self.watch_texts(); next_texts = time.time() + 3
                if now >= next_status:
                    self.watch_stack()
                    self.log('estado: arena ' + self.arena.describe()); next_status = now + 60
                time.sleep(0.02)
            except PineError as ex:
                self.log('PINE: %s; tentando de novo em 5s' % ex)
                time.sleep(5)
            except OSError as ex:
                self.log('Conexao perdida (%s); tentando reconectar em 5s' % ex)
                time.sleep(5)
                try:
                    self.pine = Pine(self.args.port)
                except OSError:
                    pass


def newest_iso():
    isos = sorted(ROOT.glob('work/output/ACE2-EN-*.iso'), key=lambda p: [int(x) for x in re.findall(r'\d+', p.stem)])
    return isos[-1] if isos else None


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=('watch', 'check'))
    ap.add_argument('image', nargs='?', help='check: RAM dump (.bin) or savestate (.p2s)')
    ap.add_argument('--iso', type=Path, default=newest_iso())
    ap.add_argument('--port', type=int, default=28011)
    ap.add_argument('--slot', type=int, default=10, help='savestate slot written by the dumps (overwritten)')
    ap.add_argument('--interval', type=float, default=0.5)
    ap.add_argument('--pcsx2', type=Path, action='append', help='PCSX2 folder (sstates/, logs/)')
    args = ap.parse_args()
    if not args.iso or not args.iso.exists():
        raise SystemExit('ISO de teste nao encontrada (use --iso)')
    args.pcsx2 = [p for p in (args.pcsx2 or PCSX2_DIRS) if p.exists()]
    if args.cmd == 'watch':
        Watch(args).run()
        return
    if not args.image:
        raise SystemExit('check: informe o dump da RAM ou o savestate')
    ram, regs = load_image(args.image)
    for line in analyse(ram, regs, catalog(args.iso)):
        say(line)


if __name__ == '__main__':
    main()
