# Making and sharing your own patch

This guide is for anyone who builds the English ISO from this repository (with or without their own text changes) and
wants to give it to other people. You never share the ISO: you share an **xdelta patch**, a file of about 40 MB
(instead of a 3.6 GB image) that turns the untouched Special Vocal Version into your English disc. Players apply it
with any xdelta patcher, exactly like the project's own releases ([INSTALL_PATCH.md](INSTALL_PATCH.md)).

The project makes its releases with the same tool you use here, `tools/ace2/make_patch.py`.

## The whole thing in short

PowerShell, in the repository root, after [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md) steps 1–4:

```
$env:PYTHONIOENCODING = 'utf-8'
# optional: edit work\translation\en\_fill\<table>.json (MAKE_YOUR_OWN_TRANSLATION.md), then
.venv\Scripts\python.exe tools\ace2\merge_fill.py --check
.venv\Scripts\python.exe tools\ace2\merge_fill.py
# build, audit, patch
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17-yourname --write
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17-yourname.iso
.venv\Scripts\python.exe tools\ace2\make_patch.py --version 0.0.17-yourname --xdelta3 C:\tools\xdelta3.exe
```

Result in `work/release/`: `ACE2-EN-0.0.17-yourname.xdelta` and `ACE2-EN-0.0.17-yourname-SHA256.txt`. Share those
two files.

**No 2006 disc?** Add `--svv-opening` to all three of the last commands (the build and the audit then use
`ACE2-EN-0.0.17-yourname-svv-opening.iso`; the patch keeps the same name). The patch is the same either way: patches
never contain the 2006 opening.

## What you need

- The repository set up as in [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md), steps 1–4: the clone, the Special Vocal
  Version ISO in the root (the 2006 ISO is optional), Python 3.12 or newer with `requirements.txt`, and the fonts.
- **xdelta3**, the command-line tool (step 4 below).
- Free disk space: about 11 GB while `make_patch.py` runs (the build, a copy of it and a decode check, 3.7 GB each;
  the copy is not made with `--svv-opening`). The check copy is deleted automatically.
- Optional: a GitHub account, to publish the patch as a release of your own fork (step 7).

## 1. Pick a version name

The version is only a name: it goes into the file names and the checksum file, and it does not change the image.
Use the project version your work starts from plus your name, for example `0.0.17-alex`, then `0.0.17-alex.2` for
your next build. **Never use a bare project number** (`0.0.17`, `0.1.0`): players must be able to tell your patch
from the project's. Use only letters, digits, dots and dashes.

## 2. Change the text (optional)

Everything about editing lines is in [MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md): where each line
lives, the rules that keep the game from freezing (widget capacity, control codes), and `merge_fill.py`, which
refuses lines that would break the game. Run `merge_fill.py --check` until it reports no `ERROR`, then
`merge_fill.py` to merge.

If you change nothing, you get the project's current version; your patch then gives players the same disc as the
project's patch, as long as your build picked the same fonts (see [below](#why-your-checksums-can-differ-from-the-projects)).

## 3. Build, audit and test

```
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17-yourname
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17-yourname --write
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17-yourname.iso
```

- The first command is a dry run: it validates every line and writes nothing. The second writes the image and ends
  with `PASS: extents, every file payload and every changed resource verified. SHA-256 …`.
- The audit must end with `PASS: layout, files, opening movie, text integrity, control tokens and mission memory`.
  **Do not share a build that did not pass the audit.**
- Play the parts you changed in PCSX2, booting normally (not from a save state):
  [BUILD_FROM_SOURCE.md, step 8](BUILD_FROM_SOURCE.md#8-play--test-in-pcsx2). A line that is too long for its widget
  can freeze the game minutes later, far from the line itself, so test the whole scene.

Without the 2006 disc, add `--svv-opening` to the build and audit commands; the image is then
`work\output\ACE2-EN-0.0.17-yourname-svv-opening.iso`.

## 4. Install xdelta3

Use **xdelta3 3.0.11**, the version the project's patches are made with and the one most patcher front-ends (Delta
Patcher, xdelta UI) are built on.

- **Windows:** download `xdelta3-3.0.11-x86_64.exe.zip` from
  [github.com/jmacd/xdelta-gpl/releases/tag/v3.0.11](https://github.com/jmacd/xdelta-gpl/releases/tag/v3.0.11),
  extract it and rename the `.exe` to `xdelta3.exe`. Either put its folder on `PATH` or give its full path to
  `make_patch.py` with `--xdelta3` (as in the commands above).
- **Linux:** `sudo apt install xdelta3` (Debian/Ubuntu), `sudo dnf install xdelta` (Fedora).
- **macOS:** `brew install xdelta`.

Check it: `xdelta3 -V` (or `C:\tools\xdelta3.exe -V`) prints `Xdelta version 3.0.11`.

## 5. Make the patch

```
.venv\Scripts\python.exe tools\ace2\make_patch.py --version 0.0.17-yourname --xdelta3 C:\tools\xdelta3.exe
```

(`--svv-opening` if you built with it. Leave out `--xdelta3` when `xdelta3` is on `PATH`. Linux/macOS:
`.venv/bin/python tools/ace2/make_patch.py --version 0.0.17-yourname`.)

It takes a few minutes and checks every step:

1. **Special Vocal opening.** A normal build carries the 2006 "Glorious" movie, which must not go into a patch. The
   tool copies your build to `work/release/ACE2-EN-<version>-svv-opening.iso` and puts the Special Vocal movie back
   (`swap_movie.py`). With `--svv-opening` your build already has it, and no copy is made.
2. **Encode** the patch from the untouched Special Vocal Version: `xdelta3 -e -9 -B 1073741824`. The 1 GB source
   window is needed because the build moves some files to the end of the disc.
3. **Decode check:** applies the new patch to the untouched ISO again and compares the result with the image, byte
   for byte.
4. **Checksums:** recomputes what a player gets after adding "Glorious" with `swap_movie.py` and requires it to be
   your build's SHA-256 (with `--svv-opening`, the patched image itself must be your build). Then it writes the
   checksum file.

It ends with `PASS: work\release\ACE2-EN-0.0.17-yourname.xdelta (… bytes), ACE2-EN-0.0.17-yourname-SHA256.txt`.

| File in `work/release/` | What it is |
|---|---|
| `ACE2-EN-<version>.xdelta` | the patch: untouched Special Vocal Version → your English disc (Special Vocal opening) |
| `ACE2-EN-<version>-SHA256.txt` | the input disc, the patch, the output with each opening and both movies; players check their files against it |
| `ACE2-EN-<version>-svv-opening.iso` | only the check copy of step 1: delete it once you are done |

`work/release/` and every `.xdelta` are ignored by git, so the patch never ends up in a commit by accident.

## 6. Apply your patch yourself (recommended)

Do what a player will do, with the untouched ISO, and compare the result with your checksum file:

```
xdelta3 -d -s "Another Century's Episode 2 - Special Vocal Version (Japan).iso" work\release\ACE2-EN-0.0.17-yourname.xdelta ACE2-EN-0.0.17-yourname.iso
Get-FileHash ACE2-EN-0.0.17-yourname.iso
```

The hash must equal the line "Output after the patch (Special Vocal opening)" of `ACE2-EN-0.0.17-yourname-SHA256.txt`.
If you have the 2006 disc, `swap_movie.py` on that output must give the "Glorious" line
([GLORIOUS_OPENING.md](GLORIOUS_OPENING.md)).

## 7. Share it

Share **only** these files:

- `ACE2-EN-<version>.xdelta`
- `ACE2-EN-<version>-SHA256.txt`
- optionally `tools/ace2/swap_movie.py`, for players who want the "Glorious" opening (one file, Python standard
  library only)

**Never** share an ISO, a `.PSS` movie, PCSX2 save states (`.p2s`) or RAM dumps: they contain the game itself.

### Option A: a release on your own GitHub fork

This keeps your text changes public next to the patch, so anyone can see what you changed and rebuild it.

1. On the project's GitHub page, click **Fork**. You get `https://github.com/<you>/<fork name>`.
2. Commit your changes to the fork and tag the version:

   ```
   git remote add myfork https://github.com/<you>/<fork name>.git
   git switch -c my-version
   git add -A
   git status
   git commit -m "0.0.17-yourname: <what you changed>"
   git tag -a v0.0.17-yourname -m "English patch 0.0.17-yourname"
   git push myfork my-version --tags
   ```

   In `git status`, only text files must appear: `work/translation/…json`, the build report
   `work/output/ACE2-EN-<version>.json`, maybe `docs/` or `tools/`. If an `.iso`, `.xdelta`, `.PSS`, `.p2s` or `.7z`
   shows up, stop: the `.gitignore` was changed or the file is somewhere unexpected.
3. On your fork: **Releases → Draft a new release** → choose the tag `v0.0.17-yourname` → title, for example
   `ACE2 English Patch 0.0.17-yourname` → write the notes (template below) → attach the `.xdelta`, the
   `-SHA256.txt` and `swap_movie.py` → tick **Set as a pre-release** if it is not fully tested → **Publish release**.

   With the [GitHub CLI](https://cli.github.com/) instead:

   ```
   gh release create v0.0.17-yourname work/release/ACE2-EN-0.0.17-yourname.xdelta work/release/ACE2-EN-0.0.17-yourname-SHA256.txt tools/ace2/swap_movie.py --repo <you>/<fork name> --title "ACE2 English Patch 0.0.17-yourname" --notes-file notes.md --prerelease
   ```

To bring later project updates into your fork: `git pull origin main` (where `origin` is the project), fix any
conflict in the JSON files, then build and patch again with a new version name.

### Option B: anywhere else

Upload the two files (and `swap_movie.py`) wherever you like, together with the notes below. Players follow
[INSTALL_PATCH.md](INSTALL_PATCH.md) with your file names.

### Option C: send your fixes to the project

If you fixed lines that the project should have too, open a pull request with the changed JSON files (not the patch):
see [MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md#where-the-project-keeps-corrections) for where each
kind of correction goes, and [reporting a bad line](MAKE_YOUR_OWN_TRANSLATION.md#reporting-a-bad-line).

### Notes template

```markdown
Unofficial English patch **0.0.17-yourname** for Another Century's Episode 2 – Special Vocal Version
(PS2, SLPS-25829), based on <project link> 0.0.17. <What you changed.>

## Files
- `ACE2-EN-0.0.17-yourname.xdelta` – apply to your untouched Special Vocal Version ISO
- `ACE2-EN-0.0.17-yourname-SHA256.txt` – checksums of the input and of every output
- `swap_movie.py` – optional: the original 2006 "Glorious" opening (needs your 2006 disc and Python 3.8+)

## How to install
1. Check your ISO: SHA-256 `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741`.
2. `xdelta3 -d -s "<your SVV>.iso" ACE2-EN-0.0.17-yourname.xdelta ACE2-EN-0.0.17-yourname.iso` (or Delta Patcher).
3. Check the result against "Output after the patch" in the SHA256 file.
4. Optional "Glorious" opening: `python swap_movie.py --target ACE2-EN-0.0.17-yourname.iso --source "<your 2006>.iso" --out ACE2-EN-0.0.17-yourname-Glorious.iso --sha`

No game data is included. You need your own copy of the game.
```

## Why your checksums can differ from the project's

- **Fonts.** The build draws the missing letters with TrueType fonts from `C:\Windows\Fonts` (or `ACE2_FONTS`). Other
  versions of those fonts, or an extra candidate installed, give slightly different glyphs, so a different SHA-256
  ([BUILD_FROM_SOURCE.md, step 4](BUILD_FROM_SOURCE.md#4-fonts)). The disc still works. Your own checksum file is the
  reference for your patch; the `fonts` key of your build report says which fonts were used.
- **The input never differs.** Every patch, yours and the project's, applies only to the untouched Special Vocal
  Version (`efd791e7…941741`). Players with another dump (a `.bin/.cue`, a `.chd`, an already patched ISO) must
  convert or re-rip it first.
- **The patch file itself** can differ in bytes and still produce the same disc: xdelta3 stores the file names in it,
  and another xdelta3 version or other options encode differently. What matters is the output checksum.

## Troubleshooting

| Message | Fix |
|---|---|
| `FileNotFoundError: [WinError 2]` right after `2/4 xdelta3 encode` | xdelta3 is not on `PATH`: pass `--xdelta3 C:\path\to\xdelta3.exe`. |
| `Missing the build: work\output\ACE2-EN-….iso` | The version name must be the one you built with; add `--svv-opening` if you built with it. |
| `Missing the 2006 disc (…): use a build made with --svv-opening` | Build and audit with `--svv-opening`, then run `make_patch.py --svv-opening`. |
| `Output exists: work\release\…` | A previous run left files: delete them (or use a new version name). |
| `The build report is not verified` | The build did not finish: run `build.py --write` again (new version name or delete the old image). |
| `Decoded image differs from the patched image` | Disk or memory problem during the run; free space and run again. |
| `Patched + Glorious (…) != build (…)` / `Patched (…) != build (…)` | The image in `work/output` changed after it was built (opened by a tool that writes to it, or copied over). Build again. |
| xdelta3: `target window checksum mismatch` or `XD3_INVALID_INPUT` when applying | The ISO given as source is not the untouched Special Vocal Version. Check its SHA-256. |
