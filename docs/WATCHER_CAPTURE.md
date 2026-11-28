# Watcher capture

Bots now light Watchers for vision when it is safe, using the same channel a human player gets by right-clicking one. This also fixes bots standing ("staring") next to Watchers.

## Where it lives

`bots/mode_watcher_generic.lua` overrides the engine's built-in `BOT_MODE_WATCHER`. The game's `server.dll` lists mode 28 as `WATCHER`, between `BOT_CHALLENGE_MODE_ENDGAME` (27) and `WISDOM_SHRINE` (29). It implements the mode in `dota_bot_mode_watcher.cpp` and loads overrides with the pattern `mode_%s_generic.lua`, which is how `OUTPOST` becomes `mode_outpost_generic.lua`.

## Why: the staring

The 26 Nov game's console log (`console.9107053935.log`) shows mode 28 active in 144 of 870 bot samples between minutes 10 and 20 (17%) and 174 of 1329 after minute 20 (13%). It is the mode in most stretches where a bot's distance to the Roshan pit stayed flat for 30–74s. Farm mode was already fixed (`X.FilterAttackable`, 2239b28) and loaded in that game. The staring came from the engine's default Watcher mode, which the repo never overrode. Mode 29 (Wisdom Shrine) and 30 (Lotus Pool) never appeared in that log, so they are left to the engine for now.

## Game data (d2vpkr, confirmed)

- Unit `npc_dota_lantern`: neutral team, building-class, 800/450 day/night vision.
- Ability `ability_lamp_use`: unit-target channel, cast range 200, channel time 1.0s, `active_duration` 420, `inactive_duration` 120.
- Engine modifiers `modifier_watcher_state` and `modifier_watcher_buff` exist. The trace logs whether a Watcher has them.
- Mechanics (Dota 2 Wiki; Liquipedia blocks automated fetches): channelling a neutral Watcher lights it for your team for 7 minutes. Channelling an enemy-lit Watcher turns it off and makes it untargetable for 2 minutes.

**Not confirmed:** the name `GetUnitName()` returns at runtime. Outposts report a map display name (`#DOTA_OutpostName_North`) instead of their class. The matcher therefore accepts any non-hero unit whose name contains `lantern` or `watcher`. It is also unconfirmed whether a lit Watcher's `GetTeam()` switches to the capturing team. The trace below answers both questions.

## Behaviour

- **Who:** pos 4/5 detour up to 2000 units (1200 during laning). Cores only take a Watcher within 800 units, and never during laning. Invoker is excluded, as the outpost mode does.
- **When:** HP at least 50%. No enemy hero visible within 1600 of the bot or the Watcher, and none seen there in the last 5s. Not retreating, defending, fighting, damaged by a hero in the last 4–5s, doing Roshan/Tormentor, or behind on alive heroes. Not while the team is pushing tier 2 or high ground, and not while enemies are near our ancient.
- **Which:** the closest Watcher that is not on our team. A neutral one gets lit; an enemy one gets turned off. One bot claims each Watcher, so two supports don't walk to the same one.
- **Desire:** 0.25–0.5, rising as the bot gets closer, so it is opportunistic and loses to laning, fights and objectives. During the channel it is 0.75, and drops to 0 if the situation turns unsafe.
- **Memory:** a Watcher we lit is skipped for 420s and one we turned off for 120s, even if `GetTeam()` doesn't change. A cast that never starts channelling (3s timeout) or gets interrupted backs that bot off the Watcher for 30s, so nothing loops.
- The farm-mode fix (`X.FilterAttackable` in `mode_farm_generic.lua`) is untouched. Watchers are still never attack targets.

## How to check it in a game

1. Copy or merge this branch into the checkout your Dota `vscripts/bots` symlink points at. Host a lobby with **local** bot scripts, not the Workshop version.
2. Open the console. `WATCHER_TRACE` is on by default and prints lines starting `[OHA_WATCHER]`, even with `DebugMode` off:
   - `unit name=... team=... invuln=... attackImmune=... matched=... stateMod=... buffMod=...` prints once per nearby non-hero unit that is invulnerable, attack-immune or Watcher-named, and again when its team changes. **Check that the Watcher lines show `matched=true`.** If they show some other name with `matched=false`, add that name to `IsWatcher()`.
   - `scan watchers=N` shows how many Watchers the bot knows about. Expect it to grow as bots see more of the map.
   - `cast ability_lamp_use ...`, then `lit watcher ... teamAfter=X` or `turned off enemy watcher ...`. **`teamAfter` should be your team's number (2 = Radiant, 3 = Dire).** If it stays 4 (neutral), ownership comes from the 420s memory only, so tell Claude.
   - `cast never started channelling` or `no ability_lamp_use ability` means the cast path doesn't work at runtime. Report the line.
3. **Staring check:** no bot should stand next to a Watcher for more than a couple of seconds. After the game, the `[OHA_ROSHAN]` lines should show far less `active_mode=28` than the 13–17% seen on 26 Nov.
4. Watch a support in the first ten minutes. When a lane is quiet it should walk to the nearest Watcher, channel for about a second, and the Watcher should glow in your team's colour.
5. Check that it does **not** go when an enemy hero is visible nearby, while it is retreating or low, or to a Watcher that is already yours.
6. When you are satisfied, set `WATCHER_TRACE = false` at the top of `bots/mode_watcher_generic.lua` to quiet the console.
