# Technical reference

File formats of Another Century's Episode 2 — Special Vocal Version (SLPS-25829), the engine limits that the
translation must respect, how the tools rebuild the disc, and what each script does. The working notes this comes from
are in Portuguese in `docs/ESTUDO_ACE2.md` (section 8 has the investigations) and `docs/CHANGELOG.md`.

Translation target: English in 1-byte ASCII inside CP932 (Shift-JIS) strings, as in the ACE1 and ACE3 English
patches.

## Discs

| Use | Image | Executable | `DATA.BIN` |
|---|---|---|---|
| Base of every build | Special Vocal Version (Japan) | `SLPS_258.29` | 1,315,378,208 bytes, 5,867 resources |
| Opening movie only | Original 2006 release (Japan) | `SLPS_256.23` | — |

The executable opens `DATA.BIN` **by name** (`\DATA.BIN;1`), not by sector, so `DATA.BIN` can grow: the files after
it move into the empty tail of the disc (~20 MB free) and the ISO9660 and UDF records are rewritten.

## Why the earlier fan patch was not reused

An independent audit (`tools/ace2/audit_iso.py`) of the previous English patch found: fonts never completed (text in
fullwidth capitals, 2 bytes per letter, no apostrophe or comma); text written in place within the Japanese byte budget,
leaving 160 unreadable tables, briefing pointers outside their resource and one resource moved on top of a texture;
2,097 lines with altered control codes (`<ab()>`, `<ed()>`, `<op()>`, `%d％` → `%d%%`), strong candidates for its
crashes; and an extractor that numbered resources by index position instead of ID (the IDs have gaps), so its text
was shifted to the wrong missions. Everything here was re-extracted from scratch, and its files are not used.

## Formats

The parsers come from the ACE3 English patch (MIT), via the ACE1 project; the `DATA.BIN` index, the mission
container layout and the `VMD` packages were worked out here. `tools/ace2/ace2lib.py` has the layouts in its
docstrings.

| Item | Format |
|---|---|
| `DATA.BIN` | `BND\0` index binder, 36-byte header: +12 total size, +16 count, +24 `0x30800` (kept). 12-byte entries `(id, offset, size)`. IDs ascending **with gaps**, payloads 2048-aligned, no names. |
| Inner binder | `BND\0`, `(id, offset)` pairs, payloads 32-aligned |
| LZSS | ACE3 variant: `00 01 00 00` + big-endian unpacked size. False signature positives handled by `try_unpack`. |
| Text table | magic `0x10000`, ranges, pointer array, CP932 string pool |
| Mission container | `00 01 00 00`; +4 list C (or total size); +8 list A; +12 list B; +16 list D; **+20 dialogue table**; +24 second table; +28 counts of A, B, D, C; +32 last section. Lists A, B, D: 16-byte records `(id, offset, 0, 0)`, list A = one-row sub-tables of enemy names; list C: `(id, name table, 256×128 portrait, 0)` |
| `VMD` model package | chain of chunks (`magic`, size), 16-aligned, walked by size (no chunk offset stored anywhere), ending in `END\0`. Partner packages hold text in `PMS\0` (battle chatter) and `PPN1`/`PPN2` (pilot names): a 16-byte chunk header, a text table, then leftover strings no pointer reaches. `FNM` (model name) is not extracted. |
| Font | map `00 00 01 00` (height at +8, 24-byte records: 4 float UV + int16 offset, width, advance) + TIM2 4-bpp atlas (PSMT4, linear or PSMCT32-swizzled) |
| Movies | `/MOVIE0/MOVIE001.PSS` (opening), `MOVIE002.PSS`: MPEG-2 program streams with audio |

Mission containers come in twins (`6###` and `42###`) whose sections are byte-identical at different offsets: the
sections hold no container offsets, which is what allows a table to grow in place while the sections after it move.

### Where the text is

| Content | Resources | Unique lines |
|---|---|---|
| Mission dialogue, objectives, counters | `6005–6998` and twins `42xxx` (identical lines) | 6,583 in 106 tables |
| Enemy names (lock-on HUD) | one-row sub-tables inside the mission containers | 89 |
| Partners' battle chatter | `VMD` packages `2NNN` (partner `pNNN`) and their LZSS copies `36300+NNN`, chunk `PMS` | 6,138 in 107 tables |
| Partners' pilot names | the same packages, chunks `PPN1`/`PPN2` | 51 |
| Briefings, debriefings, reports | `63000–63300` | 1,588 in 168 tables |
| Menus, encyclopedia, logs | bundles `62050–62057` (inner `3000–3077`), copies in `5000`, `120` | 2,171 in 44 tables |
| Gameplay HUD | bundles `38000–38006` (inner `3013`, `3020`, `3021`, `3024`) | 256 |
| System windows | `8031` (+ copies in `8033`, `60000`) | 8 |

In total 1,741 text locations, grouped into 434 logical tables. Not extracted yet: the second table of 76 mission
containers (offset `+24`: object and target names on the HUD, 116 rows), a few textures with Japanese, the
memory-card save title in the executable, the movies ([STATUS.md](STATUS.md#not-translated-yet)).

### Control codes

Preserved in the same order (`tools/ace2/validate.py`, and again by the audit): tags
`<sp()> <ab()> <op()> <ed()> <on()> <off()> <im()> <fz()> <tr()> <of()> <cs()> <ac()>`; colors `#c[RRGGBB]…#c`;
`#i…#i` (rank names); variables `%d`, `%s`, `%%`; button and unit icons, which are glyphs of the font:
`○ × △ □ ㊤ ㊦ ㊧ ㊨ ① … ⑳ ㍉ ㌢ ㌔ ㍍`. The fullwidth `％` after `%d` is a **literal**: turning it into `%%` changes the
printf semantics (one of the old patch's errors).

## Engine limits

Found while investigating the freezes of the test builds with `tools/research/crash_watch.py` (PCSX2 PINE) and the
disassembly of `SLPS_258.29`. Addresses are virtual addresses of the executable.

### Memory

```
0x00100000 .. 0x003afd80   executable
0x003afe00 .. 0x01d3ff00   memory arena (0x01cfff00 in the original): every scene and mission is loaded here
0x01d3ff00 .. 0x01f3ff00   second area (2 MB), follows the arena end
0x01f40000 .. 0x02000000   main thread stack, 768 KB (1 MB in the original; at most 161 KB used)
```

The arena allocator (state at `0x00345040`) allocates bottom-up, takes one block from the top, and returns NULL when a
request does not fit; the game never checks. A mission loads its container whole, and the partner packages stay
resident during the mission, so **no resident resource may carry dead bytes**: each table is rebuilt where the
Japanese one was (`ace2lib.mission_relayout`, `vmd_replace`), and `audit_iso.py` fails a mission container that grows
more than its text tables. In 0.0.17 the largest mission container grows +800 bytes (6010), all of them together
−12,048 bytes, partner packages at most +512 bytes; the arena has 256 KB more than the original.

### Text widgets

Every text widget reserves its glyph buffer once, from a capacity in characters, and the glyph builder (`0x1a1050`)
writes one sprite per character (spaces included) without checking it. Text longer than the capacity overwrites the
next object in the arena, and the game freezes later, when that object is used. There are two widget classes: init
`0x289bd0`, buffer (7n + 11) × 16 bytes for n characters, and allocator `0x28a0f0`, buffer (11n + 12) × 16 + 32
bytes.

| Widget | Capacity (characters) | Enforced by |
|---|---|---|
| Default for both classes, when the owner sets none (init `0x289dfc`): objectives, HUD counters (label + "：" + value in one widget), labels, names, MISSION INFORMATION conditions, pause help line | **32** | validator rules `widget` and `counter` |
| Message window (`0x292700`) | 60 in the original, **128** with the `exe.py` patch; its text is also copied into a 128-byte field | validator rule `message`: 127 visible bytes |
| Pause menu items / titles / unknown pause widgets | 16 / 20 / 20 and 24 | not yet |
| Menu screens (`0x28aa20`) | 42, 50, 64, 80, 120, 255, per screen | not mapped yet |

The Japanese never comes near these capacities (its messages stop at 60 characters, its objectives at 16).

## Executable patches

`tools/ace2/exe.py` is the only change to `SLPS_258.29` (four 32-bit words; the file keeps its size), applied by every
build and checked by the audit:

| Address | Original → new | Effect |
|---|---|---|
| `0x10019c` | `3c0501f0` → `3c0501f4` | stack base `0x01f00000` → `0x01f40000` |
| `0x1001a0` | `3c060010` → `3c06000c` | stack size 1 MB → 768 KB (top stays at `0x02000000`) |
| `0x12b268` | `3c0201f0` → `3c0201f4` | heap end `0x01f00000` → `0x01f40000`: arena +256 KB |
| `0x292704` | `2405003c` → `24050080` | message window capacity 60 → 128 characters |

`python tools/ace2/exe.py` prints them, checked against your base disc. Because the executable changes, PCSX2 computes
a different CRC for the English disc.

## Fonts

Four distinct fonts in 13 bundles; every copy is patched.

| Font | Where | Atlas | Height | Style | Native ASCII | TrueType chosen by calibration |
|---|---|---|---|---|---|---|
| 2500/2000 | gameplay `38000/1/4/5/6` | 1024×512 | 19 | Mincho (serif) | `% 0-9 M k` | Times |
| 2500/2000 | gameplay `38002/3` | 512×512 | 21 | Mincho | partial | Times |
| 2500/2000 | menus `62050–62054`, `62057` | 1024×512 | 19 | Mincho | partial | Georgia |
| 2501/2001 | gameplay `38000–38006` (HUD) | 256×256 | 16 | Gothic | full alphabet | Yu Gothic Regular |

`tools/ace2/fonts.py`, for each printable ASCII code 0x20–0x7E: keeps a native ASCII glyph; otherwise reuses the
pixels of the fullwidth glyph with a new, cropped record (digits share one width so numbers stay tabular);
otherwise renders the letter from the TrueType face that best matches the native glyphs (chosen by pixel comparison
among 9 candidates, sized by the native cap height), quantized to the palette's ink levels, outlined with the same
1-px dark border as the natives, and placed in free atlas space. The candidates are read from `C:\Windows\Fonts`, or
from the folder in the `ACE2_FONTS` environment variable.

- Coverage lives in the palette luminance (grey 32…~180; every color has alpha 128), not in alpha.
- The gameplay atlas is almost full: a new cell may overlap the transparent part of another cell, but ink never
  lands in someone else's cell. Guard space is decided from the data (the 2500 fonts already touch neighbours, so the
  game samples by point; the 2501 gets 1 px).
- **No original glyph, record or pixel changes** (checked byte by byte). In the 21-px font `@` did not fit and is
  reported as `skipped`. Visual proofs: `work/proof/font_*.png`.

## Disc writer

`tools/ace2/disc.py` (`write_disc`): rebuilds `DATA.BIN` with every payload 2048-aligned in its original order;
the files after it move by `DATA.BIN`'s growth, absorbed by the empty disc tail, so the image size never changes;
ISO9660 records (both endians) and UDF file entries (with descriptor CRC and checksum) are rewritten; whole-file
swaps from another image (the movie) are copied in, and a file can be replaced by new bytes of the same size (the
executable). The output is re-read and every extent, every file payload and every changed resource is verified before
it returns. In 0.0.17 `DATA.BIN` grows 778,240 bytes and 20.2 MB of the disc tail stay free.

`tools/ace2/textdb.py`: discovers **all** tables on the disc (walking binders, LZSS payloads and `VMD` chunk chains
recursively), groups copies, and writes them back. Location strings: `6012:m` (dialogue table of mission container
6012), `6012:s219` (its sub-table 219), `62050/3004` (inner entry 3004 of bundle 62050), `1234:lz/5` (entry 5 inside
the LZSS payload of 1234), `2022:vPMS` (chunk `PMS` of `VMD` package 2022). Nothing is squeezed: every table is
rebuilt at the size it needs, in its own place, and what follows it moves (mission sections, `VMD` chunks, binder
entries).

`tools/ace2/swap_movie.py`: replaces `MOVIE001.PSS` in place when both movies have the same size (they do), without
any other change ([GLORIOUS_OPENING.md](GLORIOUS_OPENING.md)).

## Tools (`tools/ace2/`)

| Script | Purpose |
|---|---|
| `ace2lib.py` | formats: ISO9660, `DATA.BIN` index, inner binders, LZSS, text tables, mission containers (`mission_relayout`), `VMD` packages |
| `disc.py` | disc writer (above) |
| `textdb.py` | table discovery, grouping and write-back |
| `export_text.py` | exports the Japanese to `work/translation/en/<table>.json` (keeps existing English); writes `inventory.json` and `partners.json` |
| `validate.py` | per-row rules: codes, CP932, no fullwidth, no Japanese, line breaks, message window (127 bytes), widget (32 characters); `check_counters` for HUD counters |
| `merge_fill.py` | merges `_fill/<table>.json`, validates, measures widths with the completed font |
| `rewrap.py` | re-breaks lines to a pixel width (layout only) |
| `fix_names.py` | applies `work/glossary/name_fixes.json` to all English text |
| `fonts.py`, `font_proof.py` | completes the fonts; draws proof images |
| `exe.py` | the executable patches (above); run alone, prints them |
| `build.py` | `--version X` dry run; `--write` writes `work/output/ACE2-EN-X.iso` + JSON report; `--svv-opening` keeps the Special Vocal movie |
| `audit_iso.py` | independent audit of a finished image, including the executable and the mission memory check (`--svv-opening` for images built that way) |
| `swap_movie.py` | puts one disc's opening movie on another (standalone, standard library only) |
| `make_patch.py` | release patch: xdelta from the Special Vocal Version + checksum file ([RELEASING.md](RELEASING.md)) |
| `operations.py` | maps tables to the 28 operations in play order |
| `glossary.py`, `agent_docs.py` | glossary merge; translator reference docs (need the ACE3 glossary folder, see below) |
| `batches.py` | translator batches: `make`, `hand`, `status` |
| `validate_return.py` | validates a translator return; `--apply` writes it to `_fill`; `--auto` refills automatic rows |
| `review_returns.py` | side-by-side review pages |
| `check_fixes.py` | tests proposed corrections without writing |
| `test_identity.py`, `test_disc.py`, `test_textdb.py` | self-tests (see [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#5-optional-run-the-self-tests)) |

`tools/research/`: scripts used to map text, widths, textures and freezes (not part of the build):

- `crash_watch.py` (+ `crash_watch.bat`): watches the game in PCSX2 through PINE, read only: memory arena, stack use,
  loaded resources, every text widget with its capacity; saves a save state and a RAM dump when a text overflows or
  memory runs out; `check` reads a dump or save state (EE registers, stack, arena)
  ([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#9-if-the-game-freezes-crash_watch)). Its log is in Portuguese.
- `label_widths.py`: pixel widths of rows (`table`, `over`, `try`) and where a row came from (`source`).
- The others have the maintainer's path `D:\Ace 2` hard-coded at the top.

External dependency: `glossary.py` and `agent_docs.py` read the ACE3 English patch glossary from
`D:\Ace 1\ACE-3-0.9.3\ACE-3-0.9.3\work\glossary` (constant `ACE3`). Nothing else needs it: the merged
`work/glossary/names.json` is in the repository.

## Text layout limits

| Text | Limit | Source |
|---|---|---|
| Message window row (`<sp()>`) | 127 visible bytes | widget capacity (above) |
| Plain one-line row of a mission or HUD table, `menu3056`; HUD counters | 32 characters | widget capacity (above) |
| Mission dialogue, partner chatter | 2 lines, 380 px | provisional: widest Japanese line 398 px, 99th percentile 359 px |
| Briefing / report | 3 lines, 430 px | measured on a 0.0.1 screenshot (no Japanese briefing line has more than 3 lines) |
| Menu label (list buttons, option cells) | 141 px | 0.0.9 test: 141 px drawn, 154 px and up **not drawn at all** |
| Other text | widest Japanese line of the same table | provisional |

Pixel limits are in `work/ui/limits.json`; `merge_fill.py` reports wider lines as `WIDE`. Character and byte limits
are errors in `validate.py`.

## Pipeline

```
export_text.py → translation in _fill/ → fix_names.py → merge_fill.py → build.py --write → audit_iso.py → PCSX2
                                                                                └→ make_patch.py → release
```
