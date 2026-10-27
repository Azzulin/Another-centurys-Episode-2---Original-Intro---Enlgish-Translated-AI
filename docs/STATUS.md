# Project status

Updated 2026-10-27.

- **Latest build: 0.0.17** (2026-10-23). Passed the audit; **not tested in game yet**. It translates Operation 04-01,
  which was entirely in Japanese through 0.0.16, and 31 more lock-on names.
- **Latest published patch: 0.0.17** (pre-release `v0.0.17`, 2026-10-27): [INSTALL_PATCH.md](INSTALL_PATCH.md). Or
  build it from source: [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md). The older patches 0.0.16 (Operation 04-01 in
  Japanese) and 0.0.10 (freezes in Operation 12-1, partners in Japanese) are superseded.
- **Want to continue the project, or start your own translation?** [TAKING_OVER.md](TAKING_OVER.md) has the state of
  the work, the open tasks in order and where every decision is recorded.

## Summary

| Area | State |
|---|---|
| Campaign (Operations 01–28) | **6,865 / 6,865** lines translated, validated, reviewed line by line and applied |
| Partner battle chatter | **6,138 / 6,138** lines (2,657 unique) for the 107 partners, plus 51 pilot names (new in 0.0.13–0.0.14) |
| Extra missions, tutorial, flashbacks, short missions | 457 + 628 + 122 + 142 lines, applied |
| Menus, encyclopedia, messages | **2,171 / 2,171**, applied (encyclopedia and letters retranslated in full) |
| HUD, speaker labels, enemy names, system windows | complete in the tables found so far (256, 118 + 83, 120, 8); object and target names still missing, see issue 5 |
| Fonts | printable ASCII completed in all 4 fonts / 13 bundles; original glyphs untouched |
| Executable | two small patches (`tools/ace2/exe.py`): memory arena +256 KB, message window 60 → 128 characters |
| "Glorious" opening | in every build; standalone swap tool for players |
| In-game testing | 0.0.13: cutscenes and gameplay stable. 0.0.14 and 0.0.15: froze in Op 11-1 (fixed in 0.0.16). 0.0.16: Op 04-01 entirely in Japanese (fixed in 0.0.17). 0.0.17: not tested yet |

All 434 text tables found so far (1,741 locations on the disc) are in English: 16,961 rows. Until 0.0.16 the
extractor missed one mission file family (Op 04-01 and an extra mission) and many enemy-name lists. One more table
kind is known and not extracted yet (issue 5).

## Freezes found so far

Almost every freeze had the same cause: **text longer than the widget that draws it.** Every text widget of the
game reserves room for a fixed number of characters when it is created, and the drawing code never checks it. A
longer text overwrites the next object in memory, and the game freezes later, often at a moment that has nothing
to do with the text (a boss phase, the next pause). Japanese never comes near those limits; English does.

| Build | Where it froze | Cause | Fixed in |
|---|---|---|---|
| 0.0.9 | pausing during a mission | probably the pause-menu confirmations (89–96 characters in a 60-character message window) | 0.0.13 (to be confirmed) |
| 0.0.10–0.0.12 | Op 12-1, after the cutscene before the fight with Kaine | mission lines of 65–67 characters in the 60-character message window | 0.0.13: window raised to 128 (executable patch) and every message line kept within 127 bytes |
| 0.0.14, 0.0.15 | Op 11-1, on destroying the first solar facility | the HUD counter draws label + "：" + value in **one** 32-character widget: "Solar Facilities Destroyed：1 facilities" has 39. (0.0.15 had already shortened 27 objectives and pause help lines over 32 characters: real overflows, but not this freeze.) | 0.0.16: counters of Ops 11-1, 21-1 and 22-2 shortened; the build now checks every mission counter |

The validator enforces each of these limits, so the build refuses any line that would overflow a known widget
([MAKE_YOUR_OWN_TRANSLATION.md](MAKE_YOUR_OWN_TRANSLATION.md#widget-capacity-what-freezes-the-game)).

Two memory changes made while chasing the Op 12-1 freeze turned out not to be its cause, but they stay: mission
files no longer carry their old Japanese table (0.0.11), and the game's memory arena is 256 KB larger (0.0.12).

## Known issues

1. **Widgets without a rule yet.** The pause menu has items of 16 characters, titles of 20, and 52 more widgets of
   20 and 24 characters whose use is unknown. Menu screens set their own capacities (42, 50, 64, 80, 120, 255),
   not mapped screen by screen yet. Lines in those places are only checked against the Japanese width.
2. **Menu labels wider than about 141 px are not drawn** (the whole label is blank). Found in the 0.0.9 test;
   0.0.10 shortened the labels of the Intermission and Options screens, and about 300 other one-line labels are
   still over 141 px (unit names, regions, objectives, save and versus screens, whose boxes have not been measured).
   List them with `tools\research\label_widths.py over`.
3. Provisional width limits: mission dialogue (380 px) and most menus are estimated from the Japanese, not measured.
   142 lines are wider than the widest Japanese line of their table (`work/ui/wide_0.0.9.txt`).
4. The 21-px font (`38002/3`) has no `@` (no room); which screen uses this font is unknown.
5. **Object and target names still in Japanese in 76 mission files** (116 rows, 41 names), for example
   "チューリップ" (Op 04-01), "ソーラー施設" (Op 11-1) and "ギガノス基地". They sit in the second table of the mission file
   (`+24`), which the extractor does not read yet. Not a crash risk; a translation gap. (The enemy-name lists of 82+
   files, the earlier issue 5, were fixed in 0.0.17.)
6. Partner model names (`FNM` chunk, in 535 model packages) are not extracted; unknown whether they appear on screen.
7. Four partner lines show stray spreadsheet codes (`C235`, `C68`, `C183`, `+C89`) because the Japanese original
   has them; they are kept as they are.
8. **Lines longer than their widget, found after the 0.0.17 build (not fixed yet; already in 0.0.16).** A read-only
   audit of the 0.0.17 image against the widget capacities that `crash_watch` measured in game
   (`work/ui/auditoria_transbordo_0.0.17.md`, in Portuguese) found:
   - **seen in game:** the memory card messages "Checking Memory Card (PS2) in Slot 1…" (85 characters) and
     "Loading from Memory Card (PS2)…" (89) in an 80-character widget (`menu3041` #0 and #29), on every boot and
     load;
   - **almost certain:** the "Saving…" and "Formatting…" messages (`menu3041` #19, #18: 86 and 100), and two
     Free Mission objectives over 32 characters (`menu3055` #25 "Destroy the Infinite Mobile Cannon", #32 "Destroy
     Submersible Combat Vessel");
   - **probable:** about 45 one-line menu and briefing lines over 32 characters (button guides, confirmation titles,
     option names, operation titles), in tables the validator's 32-character rule does not cover yet.

   No freeze has been traced to them so far (0.0.16 was played with them), but they write past their widget the
   same way the Op 11-1 counter did. Shortening them and extending the `widget` rule to `menu*` and `brief*` is the
   first task of the next build ([TAKING_OVER.md](TAKING_OVER.md#open-tasks-in-order)). If the game freezes on a
   memory-card screen, report it.

## What to test

For 0.0.17. Boot normally, not from a save state (see [INSTALL_PATCH.md](INSTALL_PATCH.md#step-4--play)). Please
report the build, the operation/mission and a screenshot.

- **Op 04-01 to the end** (new in 0.0.17): every line, the "Chulips Destroyed" counter, and the time-out ending if
  you can. The lock-on names of Op 04-02 (Zaku II, Dowtwen, GP02). The Chulip lock-on name is still Japanese
  (issue 5).
- Lock-on names in a Free Mission or extra mission (for example Deathscythe Hell, Gundam Heavyarms, Gundam
  Sandrock).
- **Op 11-1 to the end**: destroy all 12 solar facilities (the 0.0.14/0.0.15 freeze). If you can, the counters of
  Op 21-1 ("Heavy Attackers Passed") and Op 22-2 ("Resistance Facility：HP 100％").
- **Op 12-1** through the cutscene and the fight with Kaine (the 0.0.10 freeze).
- **Memory card** (issue 8): boot, load, save, and if you can save with a full card and with no card.
- **Pause during a mission** and go through every item (Commands, Retry, To Intermission); open MISSION
  INFORMATION and COMMAND LIST.
- **Partners** from different series (Gato, Izumi, Layzner/Rei, Gon Jem): every line whole in the window, including
  the two-line ones.
- Intermission, Options > Game, Options > Controller: no blank labels.
- Briefings: three full lines inside the box. Mission dialogue: a long line near 380 px.
- Report signatures aligned with fullwidth spaces; the ending credits (`m6285`).
- Two-line objectives (Operations 06, 09, 14, 18, 22).
- The "Rei" speaker label in a Layzner mission (Op 19); "81％" and other percent signs (Op 08, Op 21).
- Pilot ranks (`menu3001`, SS, S… Ace, Rookie); the save slot "No. 00" (`menu3041#13`).
- The lines in `work/ui/wide_0.0.9.txt` and `work/translation/agent/width_waivers.json`.

If the game freezes, write down exactly what was on screen and what you had just done. Testers on Windows can run
`tools/research/crash_watch.py` next to PCSX2: it records which text overflowed at the moment it happens
([BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md#9-if-the-game-freezes-crash_watch)). Attach its `log.txt` to the
report (not the RAM dumps or save states: they contain game data).

## Not translated yet

| Where | What | Plan |
|---|---|---|
| Second table (`+24`) of 76 mission files | object and target names on the HUD (issue 5) | extract and translate |
| Texture `50641` in `62050`, `62052`, `62054`, `62057` | "プレイヤーユニット / アナザーユニット" header on unit select | translate (4 copies) |
| Texture `50019` in `38002`, `38003` | boot notice: the story is original to the game and differs from the series | translate |
| Texture `50196` in `62057` | copyright with company names in Japanese | optional (romanize) |
| Texture `50020` in `38005`, `38006` | G Gundam "明鏡止水" cut-in | probably keep |
| Executable `SLPS_258.29` (0x219150) | save title shown in the PS2 memory-card browser | optional |
| `MOVIE001.PSS`, `MOVIE002.PSS` | burned-in text not checked | check |
| Voices | audio | out of scope |

The texture census (`tools/research/texture_census.py`) found 1,655 images; only these have Japanese. New textures
must not change original pixels outside the replaced area (same rule as the fonts).

## Open decisions

- Spellings: Tak / Tack; Sinapus / Synapse; Barkholz / Barkholtz; Show / Sho; Gekiganger / Gekigangar;
  King of Hearts / King of Heart; Sarge Opus / Sarge Aupus.
- Provisional terms: 地上人 = Upper Earthling; ナナフシ = Nanafushi; トランスユニット = Trans Unit; Ｄ兵器 = D-weapons;
  ダンコフ = Dankova; 聖戦士 = Holy Warrior; ボドル基艦 = Boddole Flagship; 先輩 = "Senpai" (used in Op 21) vs
  "Senior Gale" (`m6009#22/24`); ヤルフの神 = "the god Yarf" (Black Knight, `partner064#46`).
- Misa Hayase: 早瀬大尉 = "Capt. Hayase" by the rank table, but the glossary describes her as a Lieutenant.
- Credits: uncertain readings of some staff names; long-vowel style (Satou, Ohtsuka) vs the public spelling of voice
  actors (Toru Furuya, Akio Otsuka).
- Tutorial weapons without official English names (Flame/Flare Bomb, Removed/Removable Arm, Slit Wafer…).
- The source itself is inconsistent in places (Misa is 大尉 and 中尉 in different lines; "Fifth" vs "4th" air base;
  Boddole Zer's fleet "millions" vs "5 million"); the English follows each line.

## Next steps

1. Shorten the lines of issue 8, extend the validator's 32-character rule to `menu*` and `brief*`, build 0.0.18.
2. Finish the in-game test (list above) on 0.0.17 or 0.0.18.
3. Map the 16/20/24-character widgets and the menu screens' capacities with `crash_watch.py`, and add them to the
   validator.
4. Extract and translate the second table (`+24`) of the 76 mission files, watching the memory growth.
5. Measure the menu boxes from screenshots, record them in `work/ui/limits.json`, and undo the abbreviations the
   provisional limits forced ("B. Rifle", "Sub Cann. 01"…).
6. The textures and the save title.
7. Glossary gaps (Mirauli, Sally Po, Peacemillion, Titans, Mobile Doll, Sanc Kingdom…) and the open decisions.
8. Validator: check full names, not only one word of them.
9. Publish each new build as a pre-release patch; the first regular release (0.1.0) comes once a build passes the
   in-game test ([RELEASING.md](RELEASING.md)).

Step by step, for whoever continues: [TAKING_OVER.md](TAKING_OVER.md#open-tasks-in-order).
