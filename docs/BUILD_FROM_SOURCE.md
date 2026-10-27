# Building the English ISO from source

This rebuilds the English disc from your own Special Vocal Version ISO and the translation files in this repository,
exactly as the maintainers do. Players who only want the current version (0.0.17) can apply its published patch
instead ([INSTALL_PATCH.md](INSTALL_PATCH.md)); building is for those who change the text, test the newest sources
or want to check the release. No programming is needed, only copying a few commands. To share what you built, make
an xdelta patch of it: [MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md).

Time: 5 to 10 minutes per build (planning takes 2 to 8 minutes depending on the machine and Python version, writing
3.6 GB another 2 or 3). Disk: 3.7 GB per build plus the source ISOs.

## 1. Get the repository

```
git clone https://github.com/Azzulin/Another-cecnturys-Episode-2---Original-Intro---Enlgish-Translated-AI.git "Ace 2"
cd "Ace 2"
```

(Or **Code → Download ZIP** on GitHub and extract it. To update later: `git pull`, or download the ZIP again.)

## 2. Put the ISOs in the repository root

The tools look for these **exact file names** in the repository root (next to `README.md`):

| File name | Required? | SHA-256 |
|---|---|---|
| `Another Century's Episode 2 - Special Vocal Version (Japan).iso` | **Yes** (base of every build) | `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741` |
| `Another Century's Episode 2 (Japan).iso` | Only for the "Glorious" opening (default) | `c9dcaeda5e466120c777d771639e4b247a787c84f3cc7131322f8e6dd390eef5` |

They are ignored by git (`.gitignore`), so they never get committed. Without the 2006 disc, build with
`--svv-opening` (step 6). How to check a SHA-256: [INSTALL_PATCH.md, step 1](INSTALL_PATCH.md#step-1--check-your-iso).

## 3. Python environment (Windows)

Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/) (3.12 and 3.14 both reproduce
the published builds). In the repository root, in PowerShell:

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONIOENCODING = 'utf-8'
```

(`py -3.14` if that is the version you installed; `py --list` shows them.)

- `requirements.txt` pins numpy 2.5.3, pillow 12.3.0 and pycdlib 1.21.0.
- Always call `.venv\Scripts\python.exe` (on some Windows installs a bare `python` opens the Microsoft Store).
- **`PYTHONIOENCODING=utf-8` is required** in every new terminal: the tools print game text (①, ○, Japanese), and
  the Windows console code page breaks on it. `merge_fill.py` stops half-way without it, leaving tables unmerged.
  Git Bash: `export PYTHONIOENCODING=utf-8`.
- The `.venv` folder belongs to one machine. If you copy the project to another computer, create it again there.

The commands below use Windows paths. On Linux/macOS use `.venv/bin/python` and forward slashes.

## 4. Fonts

The game fonts have no lowercase Latin letters and almost no punctuation. `tools/ace2/fonts.py` draws the missing
printable ASCII characters into free space of each font atlas, choosing, by pixel comparison with the game's own
glyphs, the TrueType font that matches best. It reads them from `C:\Windows\Fonts`. The fonts chosen for every
build so far:

| Game font | Chosen TrueType | SHA-256 of the TTF used |
|---|---|---|
| gameplay 38000/2500, 38002/2500 | `times.ttf` 18 and 21 px | `931c5de5c70401d9324d5014c123802b4fb753000360ceb2f56c589403cd58c5` |
| HUD 38000/2501 | `YuGothR.ttc` 13 px | `cd24b5617c1e26572b0a7fe7e558f7121ca42c36f7b50e8d9216ac222a1c0a93` |
| menus 62050/2500 | `georgia.ttf` 17 px | `38dffcaf1fac89492f7c56c600a14daf36ae42f7c21985cd4134ae113124a58f` |
| `\` (fallback) | `segoeui.ttf` | `704eada12961a27fd271f7d3b09e2066520e758390c1776744eff430fee30f6e` |

The build report (`work/output/ACE2-EN-<version>.json`, key `fonts`) records the choice of each build.

- A different version of these fonts, or an extra candidate installed (`CENTURY.TTF`, which comes with Microsoft
  Office), can change the glyphs and therefore the SHA-256 of the result. The game still works, but your ISO will not
  match the published checksum. Step 7 detects this.
- **Linux/macOS:** copy the candidate files (`CANDIDATES` in `tools/ace2/fonts.py`: `times.ttf`, `georgia.ttf`,
  `YuGothR.ttc`, `segoeui.ttf`…, with exactly those names) from a Windows installation into a folder and point the
  tools to it: `export ACE2_FONTS=/path/to/that/folder`. Not tested by the maintainers.

## 5. Optional: run the self-tests

```
.venv\Scripts\python.exe tools\ace2\test_identity.py
.venv\Scripts\python.exe tools\ace2\test_textdb.py
.venv\Scripts\python.exe tools\ace2\test_disc.py
```

Run them one at a time.

- `test_identity.py`: rebuilding every container without edits reproduces the original bytes: the index, the
  binders, the LZSS blocks, every text table (including the 460 tables inside partner model packages) and the 247
  mission files rebuilt in place.
- `test_textdb.py`: a synthetic translation 1.5× longer than the Japanese fits in all 1,741 text locations, with no
  dead bytes left in mission files, and the disc still has room.
- `test_disc.py`: a disc rebuilt without edits is byte-identical to the original; a grown disc with the movie swap
  verifies. Writes two temporary images in `work/output/_test` and deletes them (needs ~8 GB; slow).

## 6. Build

Dry run first (plans every change, validates every line, writes nothing, prints sizes and the fonts chosen; it
prints nothing for the first minutes while it plans):

```
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17
```

Then write the image:

```
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17 --write
```

Output: `work/output/ACE2-EN-0.0.17.iso` and `work/output/ACE2-EN-0.0.17.json` (report: tables, fonts, sizes,
SHA-256). The last line is `PASS: extents, every file payload and every changed resource verified. SHA-256 …`.

The version is only a name for the output files; it does not change the image. If you edit the text, use a name of
your own (`0.0.17-mine`) so you never confuse your image with a published one.

Without the 2006 disc:

```
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17 --svv-opening --write
```

writes `work/output/ACE2-EN-0.0.17-svv-opening.iso`, with the Special Vocal opening. Adding the 2006 movie to it
later with [swap_movie.py](GLORIOUS_OPENING.md) gives the same bytes as the normal build.

What the build does (details in [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)):

1. reads every `work/translation/en/<table>.json` row that has an `"en"` value and validates it: control codes,
   encoding, line count, and the capacity of the widget that draws it (message lines within 127 bytes, objectives,
   HUD lines and counters within 32 characters). Any failure stops the build;
2. writes the English into every copy of each table on the disc, growing and relocating tables instead of squeezing
   text into the Japanese byte budget; mission files and partner model packages are rebuilt with each table in the
   place of the Japanese one, so they carry no dead data into the game's memory;
3. completes the ASCII glyphs of the 4 fonts in all 13 font bundles, never touching an original glyph;
4. patches the executable `SLPS_258.29` (4 words, `tools/ace2/exe.py`): 256 KB more memory for the arena where
   missions load, and a message window of 128 characters instead of 60;
5. rebuilds `DATA.BIN` (it grows by about 760 KB), moves the files after it into the empty tail of the disc,
   rewrites the ISO9660 and UDF records, and swaps in the 2006 `MOVIE001.PSS` (unless `--svv-opening`);
6. re-reads the new image and verifies every file extent, every file's content and every changed resource.

The image size never changes (3,677,028,352 bytes).

## 7. Audit and compare

```
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17.iso
```

(Add `--svv-opening` for an image built with that option.) It independently re-reads the image and checks: no
overlapping files or resources; every file other than `DATA.BIN`, the movie and the executable byte-identical to the
original disc; the movie identical to the expected opening; the executable equal to the original plus exactly the
`exe.py` patches; every text table still parses with all control codes in the Japanese order; every resource
without text or font byte-identical; every mission file grown only by the growth of its text. It prints the largest
growth of the mission files and partner packages and ends with
`PASS: layout, files, opening movie, text integrity, control tokens and mission memory`.

Expected SHA-256 of the build (printed by `build.py` and stored in the JSON report):

| Image | SHA-256 |
|---|---|
| `ACE2-EN-0.0.17.iso` ("Glorious" opening) | `33fad6e583aa305123afbf4e2d6c41f6b110d6ad395cc32789d87369e2300a8d` |
| `ACE2-EN-0.0.17-svv-opening.iso` (built with `--svv-opening`) | `8e8c5ed1740faa7924ce50f10913fcb1ecfb1ace0d80185185594ffc8e1be579` |
| the `--svv-opening` image after `swap_movie.py` with the 2006 disc | `33fad6e583aa305123afbf4e2d6c41f6b110d6ad395cc32789d87369e2300a8d` (same as the normal build) |

A different SHA with `PASS` almost always means different fonts (step 4): compare the `fonts` key of your report with
the one in the repository's `work/output/ACE2-EN-0.0.17.json`. The image still works; it just is not byte-identical.

## 8. Play / test in PCSX2

- Boot the image normally. **Do not load save states** made with another build or with the Japanese disc: a save
  state keeps the old font and text in memory, so text appears garbled. Since 0.0.12 the executable differs from the
  original, so PCSX2 also sees a different CRC: old save states and `.pnach` patch files named after the original
  CRC (widescreen, cheats) do not apply. Memory card saves are fine, and PCSX2's own per-game settings (GameDB, by
  serial) still apply.
- What to look at: [STATUS.md](STATUS.md#what-to-test).
- Real PS2: the image is a normal single-layer DVD-5 image of the same size as the original; use it with whatever
  loader you already use for PS2 backups (OPL, etc.).

## 9. If the game freezes: crash_watch

`tools/research/crash_watch.py` watches the game running in PCSX2 through PINE (PCSX2's remote interface) and only
reads its memory. It lists every text on screen with the capacity of its widget, logs the memory arena and the
resources the game loads, and saves a save state and a RAM dump the moment a text overflows its widget or memory
runs out. It found the causes of the 0.0.10 and 0.0.15 freezes.

1. PCSX2 2.x: **Settings → Advanced → Enable PINE** (slot 28011). Optional: Tools → Show Advanced Settings, then
   Settings → Advanced → Logging → "EE Console", so the game's own messages go to `logs/emulog.txt`.
2. Boot the image in PCSX2, then in the repository root:

   ```
   .venv\Scripts\python.exe tools\research\crash_watch.py watch --iso work\output\ACE2-EN-0.0.17.iso
   ```

   (`tools\research\crash_watch.bat` does both steps with a double click; edit the ISO name and the PCSX2 path at
   its top first.)
3. Play. Typing a line and Enter adds a note to the log; `d` saves a save state and a RAM dump now (use it when the
   game freezes); `q` quits.

Everything goes to `work/crash/<date-time>/`: `log.txt`, RAM dumps, save states (slot 10 is overwritten) and a copy
of PCSX2's log. `crash_watch.py check <ram.bin | state.p2s>` reads a dump or a save state again later. Lines like
`TEXTO TRANSBORDA! capacidade 32, 39 letras: '…'` (the log is in Portuguese: "TEXT OVERFLOWS! capacity 32, 39
characters") name the culprit. Share `log.txt` in a report; keep the dumps and save states to yourself (they contain
game data; `work/crash/` is ignored by git).

## Troubleshooting

| Message | Fix |
|---|---|
| `Output exists: work\output\ACE2-EN-….iso` | The build never overwrites. Delete the old image or use a new version name. |
| `Expected the Special Vocal Version disc (/SLPS_258.29)` | The base ISO in the root is not the Special Vocal Version. |
| `Unexpected word at 0x…` | The executable is not the expected one: the base ISO is modified or a different dump. Check its SHA-256. |
| `FileNotFoundError: ...Another Century's Episode 2 (Japan).iso` | No 2006 disc in the root: add it or use `--svv-opening`. |
| `Validation failed: <table> ids [..]: tokens [...] != [...]` | A translated row lost or reordered a control code. Fix that row (see [MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md#control-codes)). |
| `... message window holds 127 visible bytes, this row has N` | A message line is too long for the window: shorten it. |
| `... text widget holds 32 characters, this row has N` / `HUD counter ... draws N characters` | An objective, HUD line or counter is too long: shorten it ([why](MAKE_YOUR_OWN_TRANSLATION.md#widget-capacity-what-freezes-the-game)). |
| `UnicodeEncodeError` in the console | Set `PYTHONIOENCODING=utf-8` (step 3). |
| `OSError: cannot open resource` (fonts) | A candidate TrueType file is missing; see step 4. |
| `crash_watch`: waits forever for PCSX2 | PINE is off, or on another slot (`--port`). |
