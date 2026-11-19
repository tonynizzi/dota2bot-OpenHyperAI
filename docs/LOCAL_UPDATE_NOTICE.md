# Local match-start update notice

The local fork announces its installed revision and recent changes in all-chat near match start. With the current defaults:

```text
[OHA Local 2026.09.27.1] Updates: Treant/Bounty fixes, safer ward use, and Roshan reliability.
[OHA Local] Spell/item reaction delay: 150-300 ms. Cast diagnostics: off.
```

The second line reads the effective customization, including the reaction gate's actual sanitized duration range. It reports `off` when the reaction settings are missing, disabled, or both zero. An older permanent customization file therefore cannot accidentally announce an enabled delay that is not running.

## Timing and sender

One primary bot hero is selected deterministically using the lowest actual bot player ID across both teams. The election bypasses the project's Dire ID remapping, and team-member indices are used only to verify the primary hero. It does not depend on Lua state being shared between bots. Clones, illusions, and companions cannot independently repeat the notice.

The first line is eligible from 35 seconds before the horn; the second follows at least six seconds later. Both must be sent by 60 seconds after the horn, while the game is in pre-game or in-progress state and the chosen bot is alive. A shortened pre-game can receive the messages shortly after the horn. Death/respawn does not restart the sequence. A backwards match clock resets it for a new match.

The chosen bot must be running these local scripts. A lobby mixing unrelated bot scripts may miss the notice if the elected bot does not run the hook. There is no re-election on death, avoiding duplicate notices across independent bot contexts.

The hook runs in the shared ability callback before reaction waiting, independently of laning/farming announcements and trash-talk settings. It issues only immediate chat calls, not movement or combat orders.

## Configuration

In the effective `Customize/general.lua`:

```lua
Customize.LocalUpdateNotice = false -- Mute our two local lines.
```

The default is enabled. Older override files with no `LocalUpdateNotice` field also permit the notice. `Customize.Enable = false` suppresses it. Permanent customization uses `game/Customize/general.lua`; ordinary local customization uses `bots/Customize/general.lua`.

## Updating the message

Edit `bots/FunLib/local_release.lua` when shipping a local update:

- Increment `revision` (currently `2026.09.27.1`). It identifies the installed local release metadata, not the installed game patch or an automatically computed Git hash.
- Replace `changes` with a concise summary. Keep the entire first chat line under 256 characters; the regression test checks the shipped message length.

These files are hand-written Lua and have no generated TypeScript counterpart. The upstream Workshop version and welcome messages remain as configured by upstream. This local notice makes no online requests and does not check for newer releases. It also cannot prove that every file in a partially copied installation matches the metadata.

## Validation

All 58 regression tests pass, including eight new tests for staggered output, independently running bot contexts, Dire-only bots with non-contiguous IDs, clones/deaths, disabled settings, actual reaction-window reporting, clock reset, and the production callback hook. Live in-game appearance remains to be checked in the next local match.
