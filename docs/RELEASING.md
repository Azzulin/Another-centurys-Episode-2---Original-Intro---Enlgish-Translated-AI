# Publishing a release (maintainers)

A release is an **xdelta patch from the untouched Special Vocal Version** plus a checksum file and the movie-swap
script. No ISO, no movie and no game file is ever uploaded. (Contributors who want to share a build of their own:
[MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md).)

## Versions

- `0.0.x`: internal test builds (every build gets the next number; never reuse one).
- `0.x.y`: public releases. The first public release should be the first build that passes the in-game test list
  in [STATUS.md](STATUS.md#what-to-test). Until then, publish only as a GitHub **pre-release**, with the known issues
  in the notes.

## Checklist

### 1. Build, audit, test

```
$env:PYTHONIOENCODING = 'utf-8'
.venv\Scripts\python.exe tools\ace2\build.py --version 0.1.0
.venv\Scripts\python.exe tools\ace2\build.py --version 0.1.0 --write
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.1.0.iso
```

The audit must end in `PASS`. Then test the image in PCSX2 (with `tools/research/crash_watch.py` running, if you can:
it catches text overflows the moment they happen).

### 2. Changelogs

Add the version to `CHANGELOG.md` (English, for players) and `docs/CHANGELOG.md` (Portuguese working log), with the
build SHA-256 from `work/output/ACE2-EN-0.1.0.json`. Update [STATUS.md](STATUS.md).

### 3. Install xdelta3

- Windows: download `xdelta3-3.0.11-x86_64.exe.zip` from
  [github.com/jmacd/xdelta-gpl/releases/tag/v3.0.11](https://github.com/jmacd/xdelta-gpl/releases/tag/v3.0.11)
  (the releases so far were made with 3.0.11, the version most patcher front-ends are built on), extract it, and
  either rename it to `xdelta3.exe` and put it on `PATH`, or pass its path with `--xdelta3`.
- Linux: `sudo apt install xdelta3`. macOS: `brew install xdelta`.

### 4. Make the patch

```
.venv\Scripts\python.exe tools\ace2\make_patch.py --version 0.1.0
```

(`--xdelta3 C:\path\to\xdelta3.exe` if it is not on `PATH`; `--svv-opening` for a build made with that option,
on a machine without the 2006 disc.) It:

1. copies the build and puts the **Special Vocal** opening back (`swap_movie.py`), so the patch carries no 2006
   movie;
2. encodes `work/release/ACE2-EN-0.1.0.xdelta` against the untouched Special Vocal ISO (`xdelta3 -e -9 -B 1 GB`);
3. decodes the patch again and checks the result byte for byte;
4. recomputes what a player gets after `swap_movie.py` with the 2006 disc and checks it equals the build's SHA-256;
5. writes `work/release/ACE2-EN-0.1.0-SHA256.txt` (input disc, optional 2006 disc, patch, output with each opening,
   both movies).

Delete `work/release/ACE2-EN-0.1.0-svv-opening.iso` afterwards; it is only the check copy. `work/release/` is
ignored by git.

### 5. Commit and tag

```
git add -A
git status            # no .iso, .xdelta, .PSS, .p2s, .7z or work/crash/ must appear
git commit -m "Release 0.1.0"
git tag -a v0.1.0 -m "English patch 0.1.0"
git push origin main --tags
```

### 6. Create the GitHub release

On GitHub: **Releases → Draft a new release** → choose tag `v0.1.0` → title
`ACE2 English Patch 0.1.0` → paste the notes (template below) → attach:

- `work/release/ACE2-EN-0.1.0.xdelta`
- `work/release/ACE2-EN-0.1.0-SHA256.txt`
- `tools/ace2/swap_movie.py`

Tick **Set as a pre-release** while the build has known issues → **Publish release**.

Or with the GitHub CLI:

```
gh release create v0.1.0 work/release/ACE2-EN-0.1.0.xdelta work/release/ACE2-EN-0.1.0-SHA256.txt tools/ace2/swap_movie.py --title "ACE2 English Patch 0.1.0" --notes-file notes.md --prerelease
```

GitHub accepts assets up to 2 GiB each; the patch is far smaller.

## Updating the repository from the working folder

The maintainers work in a synced folder that is **not** a git repository (it also holds the ISOs, PCSX2 captures
and the translator's quarantined files). To publish its state, copy it over a clone and let git show the
difference:

1. A clone outside the working folder, with line endings normalized the way the repository stores them (LF):

   ```
   git clone https://github.com/Azzulin/Another-cecnturys-Episode-2---Original-Intro---Enlgish-Translated-AI.git ace2-repo
   cd ace2-repo
   git config core.autocrlf input
   ```

2. Replace `tools/` and `work/` of the clone with the working folder's, and copy `docs/`, `README.md`, `CLAUDE.md`,
   `CHANGELOG.md`, `AGENTS.md`, `requirements.txt` and `.gitignore` over. Leave out the ISOs, `.venv/`,
   `__pycache__/`, `work/crash/`, `work/output/_test/`, `work/output/*.iso` and
   `work/translation/agent/_quarentena_*/` (most are in `.gitignore`, but copying them wastes gigabytes). For example,
   from Git Bash:

   ```
   rm -rf tools work
   tar -C "<working folder>" --exclude='__pycache__' --exclude='*.iso' --exclude='work/crash' \
       --exclude='work/output/_test' --exclude='work/translation/agent/_quarentena_*' \
       -cf - tools work docs README.md CHANGELOG.md AGENTS.md CLAUDE.md requirements.txt .gitignore | tar -xf -
   ```

3. `git status`: nothing unexpected deleted (a file that exists only in the repository means the working folder is
   missing it: copy it back there first), and no game data (`.iso`, `.PSS`, `.p2s`, `.7z`, RAM dumps).
4. Recommended: build from the clone (with the ISOs in its root) and check the SHA-256 equals the one in the latest
   `work/output/ACE2-EN-<version>.json`: then the repository reproduces the audited build.
5. Commit and push (step 5 above, without the tag when there is no release).

## Release notes template

```markdown
English fan translation of **Another Century's Episode 2 – Special Vocal Version** (PS2, SLPS-25829).
AI translation with automatic validation and line-by-line AI review (Claude); see the README.

## Files
- `ACE2-EN-<version>.xdelta` – apply to your untouched Special Vocal Version ISO
- `ACE2-EN-<version>-SHA256.txt` – checksums of the input and of every output
- `swap_movie.py` – optional: puts the original 2006 "Glorious" opening on the patched ISO (needs your 2006 disc and Python 3.8+)

## How to install
Step by step: docs/INSTALL_PATCH.md. In short:
1. Check your ISO: SHA-256 `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741`.
2. `xdelta3 -d -s "<your SVV>.iso" ACE2-EN-<version>.xdelta ACE2-EN-<version>.iso`
   (or Delta Patcher).
3. Optional "Glorious" opening: `python swap_movie.py --target ACE2-EN-<version>.iso --source "<your 2006>.iso" --out ACE2-EN-<version>-Glorious.iso --sha`

## Changes
<copy from CHANGELOG.md>

## Known issues
<copy from docs/STATUS.md>

No game data is included. You need your own copy of the game.
```
