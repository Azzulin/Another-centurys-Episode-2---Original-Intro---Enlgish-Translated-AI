# The original "Glorious" opening on the Special Vocal Version

The 2006 release of Another Century's Episode 2 opens with the song **"Glorious"**. The **Special Vocal Version**
(2007) has a different opening movie. Everything else this project uses comes from the Special Vocal Version, so the
tool below lets you combine the two: the Special Vocal disc with the 2006 opening.

It works on:

- the **untouched Japanese** Special Vocal Version (you just want the old opening), and
- the **English** Special Vocal Version made with this project's patch or build.

It needs both discs. No movie is distributed by this project.

## Why it is safe

Both discs store the opening as `/MOVIE0/MOVIE001.PSS`, and the two files have **exactly the same size**:

| Disc | `MOVIE001.PSS` size | Position in the image | SHA-256 of the movie file |
|---|---|---|---|
| Special Vocal Version (SLPS-25829), untouched | 275,251,204 bytes | byte 3,380,795,392 | `9daef5bde0044011e5e4ff3bc0dda12f85f43a36a0e5aed0576a8c714ac7fe3c` |
| Original 2006 release (SLPS-25623) | 275,251,204 bytes | byte 3,868,553,216 | `9f7bf19ba1c056ede9563bcca7247fbcfb86e31a98bde34eb0abfe4d6deb8599` |

So the movie bytes of the 2006 disc can be written over the movie bytes of the Special Vocal disc, in place. The
file keeps its position and size, so the ISO9660 and UDF directory records, every other file and the image size stay
exactly as they were. The game streams the movie by name and size; video and audio come together in the `.PSS`
(MPEG-2 program stream), so nothing has to be re-encoded or re-synchronized.

On the English build the movie sits at a different position (files after `DATA.BIN` moved when the text grew), which
is why the tool reads the position from each disc's directory instead of using fixed numbers. The English build also
patches the game executable (more memory, a longer message window); that has nothing to do with the movie, and the
swap works the same on any build.

## What you need

- Your Special Vocal Version ISO (untouched or English-patched), plain `.iso` (2048-byte sectors).
- Your original 2006 ISO, plain `.iso`. Expected SHA-256 of the whole image:
  `c9dcaeda5e466120c777d771639e4b247a787c84f3cc7131322f8e6dd390eef5` (4,332,388,352 bytes).
  A different dump of the same disc also works as long as the movie file is intact: the tool compares the movie
  sizes and verifies the result.
- **Python 3.8 or newer**, nothing else (no packages). Windows: install from [python.org](https://www.python.org/downloads/)
  and use `py` in the commands below. Linux/macOS: `python3`.
- The script [`tools/ace2/swap_movie.py`](../tools/ace2/swap_movie.py) (one file; download it or clone the
  repository).
- About 3.7 GB of free space if you write a new image (recommended).

## Step by step

1. Put `swap_movie.py`, your Special Vocal ISO and your 2006 ISO in one folder. Short file names make typing easier,
   for example `svv.iso` and `2006.iso`.
2. Open a terminal in that folder (Windows: Shift + right click on the folder background → "Open in Terminal" /
   "Open PowerShell window here").
3. Run:

   ```
   py swap_movie.py --target svv.iso --source 2006.iso --out svv-glorious.iso --sha
   ```

   (`python3` instead of `py` on Linux/macOS.) For the English disc, use the patched ISO as `--target`:

   ```
   py swap_movie.py --target ACE2-EN-<version>.iso --source 2006.iso --out ACE2-EN-<version>-Glorious.iso --sha
   ```

   If you built the English ISO yourself with `build.py --svv-opening`, the target is
   `work\output\ACE2-EN-<version>-svv-opening.iso` (and you can call the script as `tools\ace2\swap_movie.py` from
   the repository root).

4. Wait for the output. It shows which disc each file is and the movie hash before the copy, then:

   ```
   copying target to svv-glorious.iso
   writing /MOVIE0/MOVIE001.PSS
   PASS: /MOVIE0/MOVIE001.PSS on svv-glorious.iso is now the one from original 2006 release (SLPS-25623) (sha256 9f7bf19b...)
   image sha256 ...
   ```

   `PASS` means the movie was re-read from the new image and matches the 2006 movie byte for byte.
5. Check the image SHA-256 (printed because of `--sha`):
   - English: it must match "Output after swap_movie.py with the 2006 disc" in the release's
     `ACE2-EN-<version>-SHA256.txt`;
   - untouched Japanese Special Vocal + Glorious:
     `8030b61bd616a817be29e87315f5c41d326c166705bd306d0c5cecca766e48fb`.
6. Boot the new image and watch the opening: it is now the 2006 one with "Glorious".

### Options

| Option | Meaning |
|---|---|
| `--target FILE` | The Special Vocal image that receives the movie. |
| `--source FILE` | The image the movie is copied from (the 2006 disc). |
| `--out FILE` | Write a new image (the target is copied first and never modified). |
| `--in-place` | Overwrite the movie inside the target itself: no copy, no extra disk space, takes seconds. Keep a backup. |
| `--sha` | Also print the SHA-256 of the whole result (reads the full 3.6 GB once more). |

Undo: run it again with the **Special Vocal** disc as `--source`; the movie goes back and the image becomes
byte-identical to what it was before (tested).

## Reference checksums

| Image | SHA-256 |
|---|---|
| Special Vocal Version, untouched | `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741` |
| Special Vocal Version, untouched, with "Glorious" | `8030b61bd616a817be29e87315f5c41d326c166705bd306d0c5cecca766e48fb` |
| English build 0.0.17 with "Glorious" (what `build.py --version 0.0.17 --write` writes, and the published 0.0.17 patch + this tool) | `33fad6e583aa305123afbf4e2d6c41f6b110d6ad395cc32789d87369e2300a8d` |
| English build 0.0.16 with "Glorious" (the published 0.0.16 patch + this tool) | `888f11d1e518cd45a7b71002cd041ee087e537e592d8e6d68cb8825f5b4ac79e` |
| English build 0.0.10 with "Glorious" (the published 0.0.10 patch + this tool) | `3e8c61433aab58bafa3fb0ff6c0f55d95c63d8eefde1be441d8737be5d578c12` |
| English releases | listed in each release's `ACE2-EN-<version>-SHA256.txt` |

## How the full build does it

When you build the English disc from source ([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md)), `tools/ace2/build.py`
takes the 2006 `MOVIE001.PSS` itself while rebuilding the disc, and `tools/ace2/audit_iso.py` fails the image if the
movie is not byte-identical to the 2006 one. `build.py --svv-opening` keeps the Special Vocal opening instead (for
people without the 2006 disc); `swap_movie.py` can add "Glorious" to that image later, and the result is
byte-identical to the normal build (checked for 0.0.10, 0.0.16 and 0.0.17).

The release patch is made from the build **with the Special Vocal opening put back** (`tools/ace2/make_patch.py`), so
it never contains the 2006 movie ([RELEASING.md](RELEASING.md)).

## Questions

- **Is the audio remuxed or re-encoded?** No. The whole `.PSS` (video and audio streams) is copied unchanged.
- **Does it work for the PS3 / PS2 Classics version?** Not tested. The tool only needs an ISO9660 image with
  `/MOVIE0/MOVIE001.PSS` of the same size on both sides; it refuses anything else.
- **Can I use the 2006 disc as the base instead?** No. Its game data and executable (SLPS-25623) differ from the
  Special Vocal Version, and the translation is made for the Special Vocal data only (`build.py` refuses any other
  base).
- **Does the other movie change?** No. `MOVIE002.PSS` and every other file stay as they are.
