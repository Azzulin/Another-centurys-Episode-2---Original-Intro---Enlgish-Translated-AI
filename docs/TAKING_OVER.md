# Taking over the project (or starting your own)

This guide is for whoever wants to carry the translation on: fix what is left, test it, publish the next builds, or
take the pipeline and make a different translation (another language, another style). The original maintainers
welcome it. You do not need anyone's permission to fork; if you plan to continue the main line, open an issue on
this repository so players know where the new builds are.

Everything needed is in this repository except the game discs, which every person supplies from their own copy.

## Where the project stopped (2026-10-27)

- **Build 0.0.17**, published as a pre-release patch (`v0.0.17`). Passed the audit; **not played in game yet**.
- Every text table found so far is in English: 434 tables, 1,741 locations on the disc, 16,961 rows (campaign,
  partner chatter, menus, encyclopedia, extra missions, tutorial, HUD, names).
- All freezes found in testing had one cause, text longer than the widget that draws it, and all were fixed
  ([STATUS.md](STATUS.md#freezes-found-so-far)). A later audit found more lines over their widget (issue 8 in
  [STATUS.md](STATUS.md#known-issues)); fixing them is the first open task below.
- Still in Japanese: object and target names in the second table of 76 mission files, a few textures, the
  memory-card save title, burned-in movie text ([STATUS.md](STATUS.md#not-translated-yet)).

## 1. Set up and prove your setup

1. Follow [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md) steps 1 to 4: clone (or fork and clone), put both ISOs in the
   repository root with their exact names, create the Python environment, check the fonts.
2. Build 0.0.17 and compare with the published one:

   ```
   $env:PYTHONIOENCODING = 'utf-8'
   .venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17 --write
   .venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17.iso
   ```

   The audit must end in `PASS`, and the SHA-256 must be
   `33fad6e583aa305123afbf4e2d6c41f6b110d6ad395cc32789d87369e2300a8d` (or
   `8e8c5ed1740faa7924ce50f10913fcb1ecfb1ace0d80185185594ffc8e1be579` with `--svv-opening`). Then your machine
   reproduces the project byte for byte and every later difference is yours. A different SHA with `PASS` almost
   always means other fonts were picked ([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#4-fonts)); the image still
   works.
3. Install PCSX2 2.x (2.6.3 and 2.8.2 tested) with PINE enabled, for `crash_watch`
   ([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#9-if-the-game-freezes-crash_watch)), and xdelta3 3.0.11 if you will
   publish patches ([RELEASING.md](RELEASING.md#3-install-xdelta3)).

Your first build of your own takes the next number: **0.0.18** if you continue the main line, or
`0.0.17-yourname` for a fork of your own ([MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md#1-pick-a-version-name)).
Never reuse a number that was already built or published.

## 2. Rules that keep the disc working

These were learned from broken builds. The tools enforce most of them; do not work around a check, fix the cause.

| Rule | Why | Enforced by |
|---|---|---|
| Every build starts from the **untouched** Special Vocal Version; patches never stack | patches and audits compare against that exact image | `build.py`, `audit_iso.py` |
| A text never exceeds the capacity of the widget that draws it | the game does not check; it overwrites the next object and freezes later | `validate.py` (message window ≤ 127 bytes per line, objectives/counters/HUD ≤ 32 characters); the rest is open task 1 |
| Tables that grow are relocated, never squeezed in place | in-place writing corrupted the earlier fan patch | `textdb.py` |
| Mission files and partner packages carry no dead bytes | they sit in a memory arena with no slack | `audit_iso.py` |
| Original font glyphs are never changed; new letters only in free space | the Japanese text still uses them | `fonts.py` |
| Text is single-byte ASCII (no fullwidth letters); control codes stay in the Japanese order | the game reads codes by position | `validate.py` |
| The executable changes only by the two patches in `exe.py` | anything else is unaudited | `audit_iso.py` |
| Every image passes `audit_iso.py` before it goes to the emulator | catches layout and pointer errors before a test session is wasted | you |
| No game data in git: ISOs, `.PSS`, `.xdelta`, save states, RAM dumps | legal, and size | `.gitignore` |
| Nothing from the old "English Patched" ISO is reused (texts, extractions, injectors) | its audit found swapped lines and corrupted structures | you |

The full list, with the history behind each rule: [ESTUDO_ACE2.md](ESTUDO_ACE2.md) section 8.5 (Portuguese) and
[AGENTS.md](../AGENTS.md).

## 3. The loop for every change

```
# 1. edit the translation where that row belongs (table below)
.venv\Scripts\python.exe tools\ace2\merge_fill.py --check                        # 2. fix every ERROR
.venv\Scripts\python.exe tools\ace2\merge_fill.py                                # 3. merge
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.18 --write            # 4. build
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.18.iso  # 5. audit: PASS
# 6. play it in PCSX2 with tools\research\crash_watch.bat running
# 7. CHANGELOG.md (English), docs/CHANGELOG.md (detailed log), docs/STATUS.md
# 8. make_patch.py, commit, tag, release: docs/RELEASING.md
```

Where a fix goes depends on where the row came from (`tools\research\label_widths.py source <table>#<id>` tells):

| Origin of the row | Where the fix goes | Then run |
|---|---|---|
| Translator batch (`opNN_KK`, `xa_KK`, `xm_menuNNNN_KK`, `xp_KK`) | `work/translation/agent/reviewer_fixes.json` | `validate_return.py <batch> --apply` |
| Automatic copy (`tm` / `repeat`) | the source row, or `work/translation/auto/overrides.json` for one copy | `validate_return.py --auto` |
| Filled by hand (`hud*`, `common`, `unit_names`, `partner_names`, `m6041`, `m6907`) | `work/translation/en/_fill/<table>.json` | — |

A fix written only into `_fill` for a batch row works for your build but is overwritten the next time the batch is
re-applied. Details: [MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md#where-the-project-keeps-corrections).

Self-tests after changing any tool (one at a time, slow): `tools\ace2\test_identity.py`, `test_textdb.py`,
`test_disc.py` ([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#5-optional-run-the-self-tests)).

## Open tasks in order

1. **Shorten the lines over their widget (STATUS issue 8) and build 0.0.18.** Source:
   `work/ui/auditoria_transbordo_0.0.17.md`.
   - `menu3041` #0, #18, #19, #29 (memory card "in progress" messages) to at most 80 characters, for example
     "Checking Memory Card (PS2) in Slot 1.\nDo not remove it or turn off the power." (76).
   - `menu3055` #25 and #32 (Free Mission list) to at most 32 characters, and the same objectives in the strategic
     briefings (`brief63010` #4, `brief63013` #5).
   - Extend the `widget` rule of `tools/ace2/validate.py` (today only `m6###`, `hud*`, `menu3056`) to one-line rows
     without tags in `menu*` and `brief*` whose Japanese is at most 32 characters, then shorten what it flags (about
     45 rows: button guides, confirmation titles, option names, operation titles).
2. **Play the new build with `crash_watch`** and go through [STATUS.md](STATUS.md#what-to-test). Also open the
   screens whose widget sizes are still unknown: encyclopedia, letters, sortie help, Options, music player
   (`menu3072`), gallery (`menu3009`), and save with a full card and with no card. The `crash_watch` log lists the
   capacity of every text on screen; add what it measures to `work/ui/limits.json` and to the validator.
3. **Extract the second table of the mission files** (offset `+24`; 76 files, 116 rows, 41 names such as
   チューリップ, ソーラー施設, ギガノス基地). `+24` is already a known offset field in `ace2lib.mission_fields`; it
   needs discovery in `textdb.py`, export (probably into `unit_names`), a memory-growth check in the audit, and the
   translation.
4. **Map the remaining widgets**: pause items (16), titles (20), the 52 widgets of 20 and 24 characters, the
   capacities of each menu screen. Then undo abbreviations forced by provisional limits ("B. Rifle", "Sub Cann. 01"…,
   listed in the reviewers' reports in `work/translation/agent/review/`).
5. **About 300 one-line menu labels over 141 px**, which the game may leave blank:
   `tools\research\label_widths.py over`.
6. **Textures with Japanese** (unit select header `50641`, boot notice `50019`, optional copyright `50196`) and the
   memory-card save title in the executable ([STATUS.md](STATUS.md#not-translated-yet)). New textures must not
   change original pixels outside the replaced area.
7. **Open decisions** on spellings and terms ([STATUS.md](STATUS.md#open-decisions)), and the glossary gaps in
   ESTUDO 8.6 item 5.
8. **First public release 0.1.0**, once a build passes the whole test list ([RELEASING.md](RELEASING.md#versions)).

The same queue, with more history, is ESTUDO 8.6 (Portuguese); keep both in step when you change it.

## Where everything is recorded

| File | Language | What |
|---|---|---|
| [STATUS.md](STATUS.md) | English | state, known issues, test list, what is not translated |
| [CHANGELOG.md](../CHANGELOG.md) | English | per build, for players |
| [CHANGELOG.md](CHANGELOG.md) (docs) | Portuguese | per build, every finding, number and decision: **the most detailed record** |
| [ESTUDO_ACE2.md](ESTUDO_ACE2.md) | Portuguese | the study of the game; section 8 = current state (8.1), the batch recipe (8.3), typical translator errors (8.4), rules learned (8.5), work queue (8.6), pending decisions (8.7) |
| [RETOMADA.md](RETOMADA.md) | Portuguese | moving the working folder to a new machine |
| [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) | English | formats, engine limits, executable patches, fonts, disc writer, tools |
| [AI_TRANSLATION_WORKFLOW.md](AI_TRANSLATION_WORKFLOW.md) | English | how the batches were made, validated and reviewed |
| [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md) | Portuguese | rules and commands for AI assistants working in the folder |
| `work/ui/` | mixed | measured limits, memory growth per mission, overflow audits |
| `work/translation/agent/review/` | mixed | reviewers' reports, doubts and corrections per batch |
| `work/glossary/` | English | names and terms with their sources |

The Portuguese files are worth reading with a machine translator: most decisions are explained only there.

## Working with an AI assistant

The project was built with Claude Code. `CLAUDE.md` and `AGENTS.md` in the root are read automatically by Claude Code
(and by other agents that read `AGENTS.md`). Start each session by asking it to read
`docs/ESTUDO_ACE2.md` section 8 and the top of `docs/CHANGELOG.md`.

If you use a second AI as translator, as the project did, give it one folder: it reads
`work/translation/agent/batches/<batch>.json` and writes only `returns/<batch>.json`. Validation, review, applying,
building and auditing stay with you (or your main assistant). Whatever a translator writes outside `returns/` is
discarded and redone through the pipeline ([AI_TRANSLATION_WORKFLOW.md](AI_TRANSLATION_WORKFLOW.md)).

## Things that no longer run

- `tools/ace2/glossary.py` and `agent_docs.py` read a folder of the earlier ACE1 project (`D:\Ace 1`) that is gone.
  The build, the validation and the review do not need them; `work/glossary/names.json` is already generated. Name
  decisions now go straight into the `_fill` files or `reviewer_fixes.json`.
- The translation rules file those tools pointed to (`BASE_RULES.md`) is lost; the rules it held are summarized in
  `work/translation/agent/PLANO.md` and `PROMPT_AGENTE.md`.
- Most scripts in `tools/research/` have the maintainer's path `D:\Ace 2` at the top; edit it before running them.
  `crash_watch.py` and `label_widths.py` work from the repository.

## A different translation

The pipeline does not care which language goes into the `en` fields, within the limits of the font (ASCII today;
accents need font work): [MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md#a-translation-into-another-language).
To share the result as a patch: [MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md).
