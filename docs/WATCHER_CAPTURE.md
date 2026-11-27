# Watcher capture

Bots now light Watchers for vision when it is safe, using the same channel a human player gets by right-clicking one.

## Where it lives

`bots/mode_outpost_generic.lua`. Dota only runs mode files for its fixed mode list, so Watchers can't have a mode of their own. `BOT_MODE_OUTPOST` already handles "walk up and channel on a neutral structure". Outposts still take priority. When no outpost is wanted, the mode looks for a Watcher.

## Game data (d2vpkr, confirmed)

- Unit `npc_dota_lantern`: neutral team, building-class, 800/450 day/night vision.
- Ability `ability_lamp_use`: unit-target channel, cast range 200, channel time 1.0s, `active_duration` 420, `inactive_duration` 120.
- Mechanics (Dota 2 Wiki; Liquipedia blocks automated fetches): channelling a neutral Watcher lights it for your team for 7 minutes. Channelling an enemy-lit Watcher turns it off and makes it untargetable for 2 minutes.

**Not confirmed:** the name `GetUnitName()` returns at runtime. Outposts report a map display name (`#DOTA_OutpostName_North`) instead of their class. The matcher therefore accepts any non-hero unit whose name contains `lantern` or `watcher`. It is also unconfirmed whether a lit Watcher's `GetTeam()` switches to the capturing team. The trace below answers both questions.

## Behaviour

- **Who:** pos 4/5 detour up to 2000 units (1200 during laning). Cores only take a Watcher within 800 units, and never during laning. Invoker is excluded, as it already was for outposts.
- **When:** HP at least 50%. No enemy hero visible within 1600 of the bot or the Watcher, and none seen there in the last 5s. Not retreating, defending, fighting, damaged by a hero in the last 4–5s, doing Roshan/Tormentor, or behind on alive heroes. Not while the team is pushing tier 2 or high ground, and not while enemies are near our ancient.
- **Which:** the closest Watcher that is not on our team. A neutral one gets lit; an enemy one gets turned off. One bot claims each Watcher, so two supports don't walk to the same one.
- **Desire:** 0.25–0.5, rising as the bot gets closer, so it is opportunistic and loses to laning, fights and objectives. During the channel it is 0.75, and drops to 0 if the situation turns unsafe.
- **Memory:** a Watcher we lit is skipped for 420s and one we turned off for 120s, even if `GetTeam()` doesn't change. A cast that never starts channelling (3s timeout) or gets interrupted backs that bot off the Watcher for 30s, so nothing loops.
- The farm-mode fix (`X.FilterAttackable` in `mode_farm_generic.lua`) is untouched. Watchers are still never attack targets.

## How to check it in a game

1. Copy or merge this branch into the checkout your Dota `vscripts/bots` symlink points at. Host a lobby with **local** bot scripts, not the Workshop version.
2. Open the console. `WATCHER_TRACE` is on by default and prints lines starting `[OHA_WATCHER]`, even with `DebugMode` off:
   - `unit name=... team=... invuln=... attackImmune=... matched=...` prints once per nearby non-hero unit that is invulnerable, attack-immune or Watcher-named, and again when its team changes. **Check that the Watcher lines show `matched=true`.** If they show some other name with `matched=false`, add that name to `IsWatcher()`.
   - `scan watchers=N` shows how many Watchers the bot knows about. Expect it to grow as bots see more of the map.
   - `cast ability_lamp_use ...`, then `lit watcher ... teamAfter=X` or `turned off enemy watcher ...`. **`teamAfter` should be your team's number (2 = Radiant, 3 = Dire).** If it stays 4 (neutral), ownership comes from the 420s memory only, so tell Claude.
   - `cast never started channelling` or `no ability_lamp_use ability` means the cast path doesn't work at runtime. Report the line.
3. Watch a support in the first ten minutes. When a lane is quiet it should walk to the nearest Watcher, channel for about a second, and the Watcher should glow in your team's colour.
4. Check that it does **not** go when an enemy hero is visible nearby, while it is retreating or low, or to a Watcher that is already yours.
5. When you are satisfied, set `WATCHER_TRACE = false` at the top of `bots/mode_outpost_generic.lua` to quiet the console.
