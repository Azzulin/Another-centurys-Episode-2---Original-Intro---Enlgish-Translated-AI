# Another Century's Episode 2 — English Translation (AI-assisted) + Original "Glorious" Opening

A fan translation of **Another Century's Episode 2 — Special Vocal Version** (PS2, Japan, SLPS-25829) into English,
plus a tool that puts the **original 2006 opening movie with the song "Glorious"** back on the Special Vocal Version.

> **Status: test builds (0.0.x).** Every text table found so far is in English: the campaign (6,865 lines), the
> partners' battle chatter (6,138), menus (2,171), extra missions, tutorial, HUD and names. The latest build,
> **0.0.17**, fixes the freezes found so far and translates Operation 04-01, which was still in Japanese in 0.0.16.
> It is published as an xdelta patch (pre-release) under [Releases](../../releases) and is waiting for in-game
> testing. Read [docs/STATUS.md](docs/STATUS.md) before playing.

This repository contains **no game data**. You need your own copy of the game. Patches are published under
[Releases](../../releases); the tools here rebuild everything from your own discs.

## What do you want to do?

| I want to… | Read |
|---|---|
| Play the English version (0.0.17): apply the patch to my ISO (no programming) | [docs/INSTALL_PATCH.md](docs/INSTALL_PATCH.md) |
| Build the ISO myself from my own disc and this repository | [docs/BUILD_FROM_SOURCE.md](docs/BUILD_FROM_SOURCE.md) |
| Get the "Glorious" opening on my Special Vocal Version (English **or** untouched Japanese) | [docs/GLORIOUS_OPENING.md](docs/GLORIOUS_OPENING.md) |
| Fix or change the English text, or make my own translation (and my own ISO) | [docs/MAKE_YOUR_OWN_TRANSLATION.md](docs/MAKE_YOUR_OWN_TRANSLATION.md) |
| Make an xdelta patch of my own build and share it (my own GitHub release) | [docs/MAKE_YOUR_OWN_PATCH.md](docs/MAKE_YOUR_OWN_PATCH.md) |
| Understand how the AI translation was produced and reviewed | [docs/AI_TRANSLATION_WORKFLOW.md](docs/AI_TRANSLATION_WORKFLOW.md) |
| Know the file formats, the memory limits and how the disc is rebuilt | [docs/TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md) |
| Take over the project and continue it, or start my own from where it stopped | [docs/TAKING_OVER.md](docs/TAKING_OVER.md) |
| Publish a release or update this repository (maintainers) | [docs/RELEASING.md](docs/RELEASING.md) |
| See what is done, what is broken, what is left | [docs/STATUS.md](docs/STATUS.md), [CHANGELOG.md](CHANGELOG.md) |

### Em português (resumo)

- **Jogar:** baixe `ACE2-EN-<versão>.xdelta` em [Releases](../../releases), confira o SHA-256 da sua ISO da Special
  Vocal Version (`efd791e7…941741`), aplique com o Delta Patcher ou com
  `xdelta3 -d -s "<sua ISO>.iso" ACE2-EN-<versão>.xdelta ACE2-EN-<versão>.iso` e confira o SHA-256 do resultado no
  arquivo `ACE2-EN-<versão>-SHA256.txt`. O patch vale só para a ISO original intacta, nunca por cima de um patch
  anterior. Passo a passo (em inglês, com comandos para Windows, Linux e macOS):
  [docs/INSTALL_PATCH.md](docs/INSTALL_PATCH.md).
- **Abertura "Glorious":** precisa também da ISO de 2006 e do `swap_movie.py`
  ([docs/GLORIOUS_OPENING.md](docs/GLORIOUS_OPENING.md)).
- **Continuar o projeto ou fazer a sua tradução:** [docs/TAKING_OVER.md](docs/TAKING_OVER.md) e
  [docs/MAKE_YOUR_OWN_TRANSLATION.md](docs/MAKE_YOUR_OWN_TRANSLATION.md). As notas de trabalho mais detalhadas
  estão em português: [docs/ESTUDO_ACE2.md](docs/ESTUDO_ACE2.md) (seção 8) e [docs/CHANGELOG.md](docs/CHANGELOG.md).

## The two discs

| Disc | Serial | Used for | SHA-256 of the image (2048-byte sectors) |
|---|---|---|---|
| Another Century's Episode 2 — **Special Vocal Version** (Japan) | SLPS-25829 | **Base of everything.** Builds and patches start from this disc. | `efd791e7c50af2ec476f4026c6bda57fcf6d64babf20c12174db642b54941741` |
| Another Century's Episode 2 (Japan), **original 2006 release** | SLPS-25623 | Optional. Only its opening movie (`MOVIE001.PSS`, "Glorious") is used. | `c9dcaeda5e466120c777d771639e4b247a787c84f3cc7131322f8e6dd390eef5` |

The Special Vocal Version replaced the opening song. Both discs store the opening as `/MOVIE0/MOVIE001.PSS` with
**exactly the same size** (275,251,204 bytes), so the movie can be swapped as a whole file without rebuilding the disc
([docs/GLORIOUS_OPENING.md](docs/GLORIOUS_OPENING.md)). Patches never contain that movie: you take it from your own
2006 disc. Without the 2006 disc you can still build or patch the English version; it keeps the Special Vocal opening.

## How the translation was made (short version)

- The game's text was extracted from scratch from the Special Vocal Version: 434 text tables (1,741 locations on
  the disc), 16,961 lines, including the partners' battle chatter stored inside their 3D model packages.
- An external AI translator translated 150 batches of 80 lines in play order, with a
  glossary, per-series voice notes and the surrounding lines as context. It only ever wrote its answers to one
  folder.
- **Claude (Anthropic), working in Claude Code**, did everything else: the tools, the font work, automatic
  validation of every batch, a line-by-line meaning review against the Japanese (about 1,500 corrections), the
  partner chatter (34 batches, translated by Claude at the owner's request), the crash investigations, the builds
  and the audits.
- Every build is checked by an independent auditor (`tools/ace2/audit_iso.py`): all control codes in the original
  order, every pointer valid, no dead data left in mission files, the executable changed only by the two documented
  patches, and every other file byte-identical to the original disc.

This is a machine translation with automated and AI review, not a professional human translation. Expect awkward
lines; reports are welcome (see [docs/MAKE_YOUR_OWN_TRANSLATION.md](docs/MAKE_YOUR_OWN_TRANSLATION.md#reporting-a-bad-line)).
Details: [docs/AI_TRANSLATION_WORKFLOW.md](docs/AI_TRANSLATION_WORKFLOW.md).

## Repository layout

```
README.md, CHANGELOG.md     this file; release history in English
docs/*.md (English names)   English guides (this repo's documentation)
docs/ESTUDO_ACE2.md, docs/CHANGELOG.md, docs/RETOMADA.md, docs/REVISAO_PARALELA.md
                            the original working notes in Portuguese (the most detailed record of every decision)
AGENTS.md, CLAUDE.md        rules and commands for AI assistants working in this folder (Portuguese; Claude Code
                            reads both automatically)
requirements.txt            Python packages (numpy, pillow, pycdlib)
tools/ace2/                 the pipeline: extraction, fonts, validation, executable patch, build, audit, movie swap,
                            release patch
tools/research/             research scripts, not used by the build (widths, textures, crash_watch for PCSX2)
work/translation/en/        one JSON per text table: Japanese source + English (the build input)
work/translation/en/_fill/  English per table, by row position (what translators and reviewers edit)
work/translation/agent/     the AI-translator work package: batches, returns, validation and review reports
work/translation/auto/      rows filled automatically (exact repeats / already-translated lines)
work/translation/partners.json  who speaks in each partner table (pilot and unit)
work/glossary/              names and terms with sources; name fixes applied by script
work/ui/                    measured text-box limits, texture census, memory growth per mission
work/proof/                 font atlas proofs (images)
work/output/                build reports (JSON); the ISOs themselves are not committed
```

## Requirements at a glance

- **Players with a patch:** the Special Vocal Version ISO, an xdelta patcher, and (for "Glorious") the 2006 ISO plus
  Python 3.8+.
- **Making your own patch:** everything for building, plus xdelta3 3.0.11 and about 11 GB free while the patch is made.
- **Building the ISO / translators:** Windows (the font generator uses Windows' TrueType fonts; see
  [BUILD_FROM_SOURCE](docs/BUILD_FROM_SOURCE.md#4-fonts) for other systems), Python 3.12 or newer (3.12 and 3.14
  tested), about 8 GB free disk space.
- **Emulator tested:** PCSX2 2.6.3 and 2.8.2.

## Credits and legal

- Translation pipeline, review and builds: Claude (Anthropic) with the project owner
  ([Azzulin](https://github.com/Azzulin)).  partner chatter: Claude.
- Format codecs (DATA.BIN binders, LZSS, text tables) were first written for the Another Century's Episode 3
  English patch (MIT) and adapted through the ACE1 project.
- Another Century's Episode 2 © BANPRESTO / FromSoftware; the robots and characters belong to their respective
  rights holders (Sunrise and others). This is an unofficial, non-commercial fan project. No game files, ISOs or
  movies are distributed here. Buy the game.
