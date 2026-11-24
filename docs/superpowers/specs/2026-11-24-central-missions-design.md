# Central Missions Data — Design

## Why
Missions are identical on every server apart from translation, yet each game
update means editing one `jobs_YYMMDD.csv` per server folder in that server's
language. The CN server is retired (GL-CN replaces it). Goal: one file per
game update, written with language-neutral keys, translated only for display.

## Facts this rests on
- 6 regions rotate in a fixed loop; each has 5 fixed locations, and each
  location always has the same task text. Only the required traits change.
- gl-cn and gl-en history (18 updates each, same dates) are the same missions.

## Approaches
- **A. Location keys + translation table (chosen).** Update files list
  `location,trait_1,trait_2` as keys (`KYAROT_GREENHOUSE,KEEN,`); names come
  from `data/i18n/locations.csv`. Mirrors `pets.csv` + `traits.csv`; typos fail loudly.
- B. English names in update files, translated by exact text match. Rejected:
  fragile (e.g. curly apostrophe in `Rim’s House`), and inconsistent with trait keys.

## Design
- `data/i18n/locations.csv`: `key, region, location_<lang>, task_<lang>` for
  `en, zh_hant, ko` (no `zh_hans`: no remaining server uses it). 30 rows,
  regions numbered 1–6 in rotation order. Blank cells = no translation;
  display falls back to English.
- `data/missions/missions_YYMMDD.csv`: `location,trait_1,trait_2` (keys only).
  All 18 existing GL updates are migrated from gl-en + gl-cn; translated output
  is verified equal to the old gl-en and gl-cn files before they are deleted.
  CN-server history is dropped (its traits differed in early updates and it is
  no longer needed).
- Loader: `get_available_mission_files()` (server-independent) and
  `load_missions(path, lang)` returning the existing task dict shape
  (`task`, `bonus_skills`) so scoring/assignment are untouched. Unknown
  location or trait keys raise `ValueError`.
- Validator: every key in every missions file resolves; no duplicate location
  in a file; all locations in a file belong to one region.
- UIs (web, CLI, Tk) pick from the central mission files.
- CN removal: drop `cn` from `SERVER_LANG`, reward levels, server names, and the
  Tk GUI; default server becomes `gl-cn`; configs saying `"server": "cn"` load
  as `gl-cn`. Delete `data/cn`, `data/gl-cn`, `data/gl-en`, `data/kr` jobs files.
- KR stays listed as "not supported yet" (no Korean names in data).

## Non-goals
- No change to `pets.csv`, scoring, or the solver.
- UI language `cn` (Simplified Chinese UI) is unrelated to the CN server and stays.

## Left to the builder
Key naming for locations (UPPER_SNAKE from the English name), test layout,
and wiki wording.
