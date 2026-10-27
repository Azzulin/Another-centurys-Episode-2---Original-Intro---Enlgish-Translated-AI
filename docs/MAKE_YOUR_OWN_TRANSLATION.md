# Fixing the English or making your own translation

Everything the build puts into the game comes from plain JSON files in `work/translation/en/`. You can fix a line,
rewrite a whole scene, or start a translation into another language, and build your own ISO with the same checks the
project uses. Set up the environment first: [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md) steps 1–4.

## Your own version in short

```
# 1. edit work\translation\en\_fill\<table>.json (English by row position)
.venv\Scripts\python.exe tools\ace2\merge_fill.py --check          # 2. validate: fix every ERROR
.venv\Scripts\python.exe tools\ace2\merge_fill.py                  # 3. merge into the table files
.venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17-mine --write             # 4. build
.venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17-mine.iso    # 5. audit: PASS
```

Then test in PCSX2 with a normal boot. Add `--svv-opening` to steps 4 and 5 if you do not have the 2006 disc. To
share your version, make an xdelta patch of it, never share the ISO: [MAKE_YOUR_OWN_PATCH.md](MAKE_YOUR_OWN_PATCH.md).

Remember `$env:PYTHONIOENCODING = 'utf-8'` in every new terminal.

## How the text is stored

The game has 1,741 text locations. Copies of the same table (and twin mission files with identical lines) are grouped
into one logical table, saved as one file (434 files):

| File name | Content | Lines |
|---|---|---|
| `m6005.json` … `m6998.json` | mission dialogue (radio and cut-in lines), objectives, counters | 6,629 |
| `partner020.json` … `partner221.json` | partners' battle chatter, one file per partner (who speaks: `work/translation/partners.json`) | 6,138 |
| `brief63000.json` … `brief63300.json` | briefings, tactical briefings, debriefings, reports | 1,588 |
| `menu3000.json` … `menu3077.json` | menus, encyclopedia, messages, pilot ranks | 2,171 |
| `hud3013.json`, `hud3020.json`, `hud3021.json`, `hud3024.json` | pause menu, results, command list, speaker labels | 256 |
| `unit_names.json` | enemy names on the lock-on HUD | 120 |
| `partner_names.json` | partners' pilot names | 51 |
| `common.json` | system windows (memory card, reset) | 8 |

`work/translation/inventory.json` has per-table counts (written by `export_text.py`); `work/translation/operations.json`
says which tables belong to each of the 28 operations, in play order.

There are two files per table:

**`work/translation/en/<table>.json`: the build input.** One row per distinct Japanese line:

```json
{
 "table": "menu3004",
 "kind": "menu",
 "copies": ["62050/3004", "62057/3004"],
 "rows": [
  {"ids": [1], "jp": "選択：㊤㊦　決定：○", "en": "Select: ㊤㊦　OK: ○"},
  {"ids": [10], "jp": "インターミッション", "en": "Intermission"}
 ]
}
```

The build matches rows **by the Japanese text**, so one translation reaches every copy and every slot with the same
line. A row with an empty `"en"` stays Japanese. `copies` says where the table lives on the disc (`2022:vPMS` is the
`PMS` chunk of partner model package 2022; `36322:lz:vPMS` is its compressed copy).

**`work/translation/en/_fill/<table>.json`: what you edit.** The English by row position (0-based) in the table file:

```json
{
 "0": "Select: ㊤㊦　OK: ○",
 "2": "Intermission"
}
```

`tools/ace2/merge_fill.py` validates every fill, measures every line in pixels with the game font, and copies it
into the table file. Editing `_fill` and merging is the safe way: the merge refuses rows that would break the game.

## Fixing a line

1. **Find the line.** Search the English you saw in the game (or the Japanese) in `work/translation/en/` (any editor's
   "find in files", or `findstr /s /c:"text" work\translation\en\*.json`). Note the table and its row position
   (the n-th row of `rows`, counting from 0). Avoid `_fill` matches for this step; the position comes from the table
   file. `tools\research\label_widths.py source <table>#<id>` tells where a row came from.
2. **Edit `work/translation/en/_fill/<table>.json`**, key = row position. Keep every control code (below) and stay
   within the widget capacity (below).
3. **Check:** `.venv\Scripts\python.exe tools\ace2\merge_fill.py --check`. `ERROR` lines must be fixed; `WIDE` lines
   are warnings (the line is wider than the widest Japanese line of that table) and need a look in the game.
4. **Merge:** `.venv\Scripts\python.exe tools\ace2\merge_fill.py`.
5. **Build and audit** with your own version name so you never mix images:

   ```
   .venv\Scripts\python.exe tools\ace2\build.py --version 0.0.17-mine --write
   .venv\Scripts\python.exe tools\ace2\audit_iso.py work\output\ACE2-EN-0.0.17-mine.iso
   ```

6. **Test in PCSX2** with a normal boot (not a save state).

### Where the project keeps corrections

If you plan to send your fix back to the project, put it where the pipeline keeps that kind of row, or it will be
overwritten the next time the pipeline re-applies the translator's work:

| Origin of the row (`label_widths.py source`) | Where the fix goes | Then run |
|---|---|---|
| Translator batch (`opNN_KK`, `xa_KK`, `xm_menuNNNN_KK`, partner batches `xp_KK`) | `work/translation/agent/reviewer_fixes.json` as `{batch: {"<table>#<id>": "English"}}` | `validate_return.py <batch> --apply` |
| Automatic copy (`tm` / `repeat`) | fix the source row; for a copy that needs its own English, `work/translation/auto/overrides.json` | `validate_return.py --auto` |
| Filled by hand (`hud*`, `common`, `unit_names`, `partner_names`) | `work/translation/en/_fill/<table>.json` | — |

Then `merge_fill.py` → `build.py` → `audit_iso.py` as above. The files in `work/translation/agent/returns/` are the
translators' deliveries and are never edited. For a personal build, editing `_fill` directly is enough.

### Reporting a bad line

Open an issue with: the build version, the operation/mission or menu, a screenshot, what the line says, what it should
say (and the Japanese if you can read it). Pull requests that edit `reviewer_fixes.json` or `_fill` are welcome; say
which row (`<table>#<id>`) and why.

## Rules every line must follow

The build and `merge_fill.py` enforce most of these; the rest make the difference between text that fits and text
that disappears.

### Widget capacity (what freezes the game)

This is the most important rule. Every text widget of the game reserves room for a fixed number of characters when it
is created, and the code that draws the text never checks it. A longer text **overwrites the object next to it in
memory, and the game freezes later**, often at a moment unrelated to the text (three of the freezes found so far
were this: [STATUS.md](STATUS.md#freezes-found-so-far)). Spaces count; line breaks and control codes do not.

| Where the text appears | Capacity | Checked by the validator |
|---|---|---|
| Message window: every row with `<sp(N)>` (mission radio lines, partner chatter, briefings, reports) | **127 bytes** of visible text per row (tags and colour codes not counted; line breaks counted) | yes (`message`) |
| One-line plain rows (no tags, no line break) of mission tables `m6###` (except the credits `m6285`), HUD tables `hud*` and `menu3056`: objectives, counters, labels, names, pause help | **32 characters** (`%d` counts as 3) | yes (`widget`) |
| HUD counters: a row with `%d` right after its label row in a mission table | label + 1 + value **within 32**: "Solar Facilities Destroyed：%d" is drawn as one text | yes (`counter`) |
| Pause-menu items / titles | 16 / 20 characters | no: keep them within the Japanese width |
| Other menu screens | set per screen (42 to 255), not mapped yet | no: the 141 px label rule below applies |

The Japanese stays far below these limits, so a line that respects the widths below usually respects these too; the
exceptions are short Japanese lines that become long English ones (objectives, counters, help lines).

### Control codes

Keep every code of the Japanese line, **in the same order** (`tools/ace2/validate.py`; a mismatch stops the build):

| Code | Meaning |
|---|---|
| `<op()>` … `<ed()>` | open and close a quick mission message; a mission row without `<op()>` continues the previous message |
| `<on()>` … `<off()>` | open and close the communication window |
| `<op(N,1)>` | in briefings, speaker portrait `N` (`work/glossary/portraits.json`) |
| `<sp(N)>` | text speed; stays at the start |
| `<ab(N)>` | pause at the end of the line; `<ab(0)>` means the sentence continues in the next row |
| `<im(N)>`, `<tr(N)>`, `<of(N)>`, `<ac(N)>` | briefing images and effects; put them at the equivalent point of the sentence |
| `<fz()>`, `<cs()>` | other window codes (exact effect not documented); keep them where the Japanese has them |
| `#c[RRGGBB]text#c` | colored text: wrap the English words that match the colored Japanese words (`The #c[BE5050]Zeon remnants<im(2)>#c took...`) |
| `#i…#i` | pilot rank names in `menu3001` |
| `%d`, `%s` | numbers and names filled by the game |
| `％` (fullwidth) | a literal percent sign after a number. **Never** an ASCII `%` on its own: the game's printf reads it as a conversion |
| `○ × △ □ ㊤ ㊦ ㊧ ㊨ ① … ⑳ ㍉ ㌢ ㌔ ㍍` | controller buttons and unit icons (glyphs of the game font) |
| `　` (fullwidth space) | keep it where the Japanese uses it as a separator in menus (`Select: ㊤㊦　OK: ○`) |

A few Japanese partner lines contain stray spreadsheet codes after the text (`C235`, `C68`, `C183`, `+C89`); they are
part of the original and are kept as they are.

### Characters

- **Printable ASCII only** (letters, digits, punctuation), 1 byte each, plus the icons above when the Japanese line
  has them. No fullwidth letters, no curly quotes, no `—` em dash, no `…` (use `...`), no accented letters.
- Avoid `; ~ # $ @ [ \ ] ^ _ \` { | } * =`: some fonts had no room for them (the 21 px font has no `@`).
- No double spaces and no trailing spaces.

### Line breaks and widths

`\n` in a row is a line break inside the window. Measured or provisional limits (`work/ui/limits.json`):

| Text | Max lines | Max width |
|---|---|---|
| Mission dialogue and partner chatter | 2 per window | 380 px (provisional) |
| Briefings, debriefings, reports | 3 per window | 430 px (measured) |
| Menu labels (list buttons, option cells) | as the Japanese | **141 px**: longer labels are not drawn at all |
| Everything else | as the Japanese | the widest Japanese line of the same table |

A mission line without `<op()>` continues the previous window; a sentence split over two rows ends the first row
without a period and continues in lowercase. `tools/ace2/rewrap.py <table> [--width PX] [--lines N]` re-breaks lines
to fit (it never changes words; add `--write` to save). `tools\research\label_widths.py try menu "Some label"` measures
a candidate before you build.

### Names and terms

Use the glossary: `work/glossary/names.json` (generated from `decisions.json`, the ACE3 glossary and the researched
`research/*.json`, which cite their sources) and `work/translation/agent/GLOSSARIO.md`. Spellings that were changed
project-wide live in `work/glossary/name_fixes.json` and are applied to all text by
`tools/ace2/fix_names.py --write` (dry run without `--write`). Open decisions are listed in [STATUS.md](STATUS.md).

## A translation into another language

Possible, with one hard limit: the game stores text as Shift-JIS (CP932), and the fonts were completed only for
printable ASCII. **Accented letters (á, ç, ñ, ü…) do not exist in CP932**, so the validator rejects them.

### Without accents (works today)

1. Make a copy of the English for reference, then start from empty rows: move `work/translation/en` aside and run
   `.venv\Scripts\python.exe tools\ace2\export_text.py`. It rebuilds every `<table>.json` (partner tables included)
   from your Special Vocal ISO with empty `"en"` values (it never overwrites existing translations, so it is also
   safe to re-run). Alternatively keep the files and overwrite the `_fill` values as you go: untranslated rows stay
   English.
2. Translate into `_fill/<table>.json` (the `"en"` field name stays; it simply holds your language). You can work from
   the Japanese or from the English rows.
3. Follow the rules above, `merge_fill.py`, `build.py --version <yours> --write`, `audit_iso.py`.
4. Publish it as an xdelta like the project does: [RELEASING.md](RELEASING.md).

Words get longer in most languages: the widget capacities above are hard limits (the build refuses lines over them),
and menu labels must stay under 141 px.

### With accents (needs tool work)

Not implemented; the outline for whoever wants to do it:

- pick single-byte codes the game text never uses (CP932 `0xA1–0xDF` are half-width katakana; check the Japanese
  tables before taking them) and map each accented letter to one of them;
- teach `tools/ace2/fonts.py` to draw those letters into the free atlas space under those codes (the same way it
  draws ASCII today, without touching original glyphs) and check every font still has room (the gameplay atlas is
  almost full);
- encode the text with that mapping when tables are written (`TextTable` in `tools/ace2/ace2lib.py`) and allow the
  letters in `validate.py` and `merge_fill.widths`.

### Using an AI translator, like the project

The batch workflow (80-line batches in play order with glossary and context, automatic validation, meaning review,
application) is documented in [AI_TRANSLATION_WORKFLOW.md](AI_TRANSLATION_WORKFLOW.md). Several of its checks assume
English (glossary names, contractions); adapt `validate_return.py` and the agent instructions to your language.
