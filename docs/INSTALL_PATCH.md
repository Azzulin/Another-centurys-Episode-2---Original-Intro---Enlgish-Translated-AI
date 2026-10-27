# Applying the English patch to your ISO

This guide is for players. It takes about 10 minutes and needs no programming.

> **Which version?** Use the newest patch on the [Releases](../../../releases) page: **0.0.17** (pre-release, a
> test build being played through; known issues in [STATUS.md](STATUS.md)). It replaces 0.0.16, where Operation
> 04-01 was entirely in Japanese. Do not use the older 0.0.10: it freezes in Operation 12-1 after the cutscene, and
> its partners speak Japanese. Every patch applies to the **untouched** Special Vocal Version, never on top of an
> older patched ISO. The steps below are the same for every patch, including patches other people make from this
> repository ([MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md)).

You will end up with one of two discs:

- **English, Special Vocal opening:** the patch alone (steps 1–4).
- **English, original "Glorious" opening:** the patch, then the movie swap (steps 1–5). Needs the 2006 disc too.

## What you need

1. **Your ISO of the Special Vocal Version** (Japan, SLPS-25829), a plain 2048-byte-sector image
   (3,677,028,352 bytes). Rip it from your own disc; this project does not provide it.
2. **The patch** from the [Releases](../../../releases) page: `ACE2-EN-<version>.xdelta` and
   `ACE2-EN-<version>-SHA256.txt`.
3. **An xdelta patcher**, one of:
   - Windows: [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases) (graphical), or the
     `xdelta3` command-line tool: `xdelta3-3.0.11-x86_64.exe.zip` from
     [jmacd/xdelta-gpl v3.0.11](https://github.com/jmacd/xdelta-gpl/releases/tag/v3.0.11) (extract it and rename
     the `.exe` to `xdelta3.exe`);
   - Linux: `xdelta3` from your package manager (`sudo apt install xdelta3`, `sudo dnf install xdelta`…);
   - macOS: `brew install xdelta`, or Delta Patcher.
4. Optional, for the "Glorious" opening: your ISO of the **original 2006 release** (SLPS-25623, 4,332,388,352 bytes)
   and **Python 3.8 or newer** ([python.org](https://www.python.org/downloads/)).

## Step 1 — Check your ISO

The patch only works on the exact image it was made for. Compute the SHA-256 of your ISO and compare it with the
"Input" line of `ACE2-EN-<version>-SHA256.txt` (also in the [README](../README.md#the-two-discs)):

| System | Command |
|---|---|
| Windows (PowerShell) | `Get-FileHash "Another Century's Episode 2 - Special Vocal Version (Japan).iso"` |
| Windows (cmd) | `certutil -hashfile "Another Century's Episode 2 - Special Vocal Version (Japan).iso" SHA256` |
| Linux | `sha256sum "Another Century's Episode 2 - Special Vocal Version (Japan).iso"` |
| macOS | `shasum -a 256 "Another Century's Episode 2 - Special Vocal Version (Japan).iso"` |

Expected: `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741`.

If it differs, your dump is a different image (another region, a `.bin/.cue` of 2352-byte sectors, a compressed
`.chd`/`.cso`, or an already modified ISO). Convert or re-rip it to a plain `.iso` first; a mismatched image will make
the patcher fail or produce a broken disc.

**Do not patch your only copy.** The patcher writes a new file, but keep a backup anyway.

## Step 2 — Apply the patch

### With Delta Patcher / xdelta UI (Windows, macOS)

1. Open the program.
2. **Original file / Source:** your Special Vocal Version ISO.
3. **XDelta patch:** `ACE2-EN-<version>.xdelta`.
4. Check the options so it writes the result to a **new file** instead of overwriting your ISO (the option names
   change between versions; when in doubt, patch a copy).
5. Apply the patch and name the output `ACE2-EN-<version>.iso`.

If the graphical tool fails on this 3.6 GB image, use the command line below.

### With the command line (any system)

```
xdelta3 -d -s "Another Century's Episode 2 - Special Vocal Version (Japan).iso" ACE2-EN-<version>.xdelta ACE2-EN-<version>.iso
```

Tested with xdelta3 3.0.11 (the version the patch was made with). If another xdelta3 version stops with a window or
checksum error, add `-B 1073741824` (a 1 GB source window) right after `-d`.

## Step 3 — Check the result

Compute the SHA-256 of `ACE2-EN-<version>.iso` (same commands as step 1). It must match the line
"Output after the patch (Special Vocal opening)" of `ACE2-EN-<version>-SHA256.txt`.

## Step 4 — Play

- **PCSX2:** add the ISO to the game list and boot it. Do not load save states made with an older build or with the
  Japanese disc: a save state stores the old font in memory, so text appears garbled. Memory card saves are fine.
  From 0.0.12 on, the patch also changes two small things in the game executable (more memory, a longer message
  window), so PCSX2 reports a different CRC: save states and `.pnach` files (widescreen, cheats) made for the
  original CRC do not apply. PCSX2's own per-game settings (by serial) still do.
- **Real PS2:** the image is a normal single-layer DVD-5 image of the same size as the original; use it with whatever
  loader you already use for PS2 backups (OPL, etc.).

## Step 5 (optional) — Add the "Glorious" opening

You need the 2006 ISO and Python. Download [`tools/ace2/swap_movie.py`](../tools/ace2/swap_movie.py) (one file, no
extra packages) and run, in the folder where the files are:

```
python swap_movie.py --target ACE2-EN-<version>.iso --source "Another Century's Episode 2 (Japan).iso" --out ACE2-EN-<version>-Glorious.iso --sha
```

(On Windows, `py` instead of `python` if `python` opens the Microsoft Store.) It ends with
`PASS: /MOVIE0/MOVIE001.PSS ... is now the one from original 2006 release` and prints the image SHA-256, which must
match "Output after swap_movie.py with the 2006 disc" in the checksum file. That is the exact build the project
tested and audited.

More about the movie swap, including doing it on the untouched Japanese disc: [GLORIOUS_OPENING.md](GLORIOUS_OPENING.md).

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| Patcher says the source is wrong / checksum mismatch | Wrong input image. Check step 1. |
| xdelta3 stops with a checksum or window error | Wrong input image (step 1); otherwise add `-B 1073741824` after `-d`. |
| `swap_movie.py`: "Movie sizes differ" | The source is not the 2006 Japanese release (or is a damaged dump). |
| `swap_movie.py`: "Not an ISO9660 image" | The file is `.bin`, `.chd`, `.cso`, `.gz`…; convert it to a plain `.iso` first. |
| Garbled text right after booting | You loaded an old save state. Boot the game normally. |
| Patcher fails on an English ISO from an older patch | Patches never stack: apply the new one to the untouched Special Vocal Version. Memory card saves carry over. |
| Freeze in Op 12-1 after the cutscene (0.0.10) | Fixed since 0.0.13: use the newest patch. |
| Partners speak Japanese (0.0.10) | Translated since 0.0.14: use the newest patch. |
| Op 04-01 entirely in Japanese (0.0.16) | Fixed in 0.0.17. |
| Blank menu labels, other freezes | Known issues of the test builds: [STATUS.md](STATUS.md). Please report where it happened. |
