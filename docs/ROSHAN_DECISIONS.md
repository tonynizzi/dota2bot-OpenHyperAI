# Roshan decision review and diagnostics

## October 12, 2026 policy update

This section supersedes the historical decision order and open findings below where they conflict. Local revision: `2026.10.12.1`. Base-defense code is unchanged.

- Ancient health alone no longer vetoes Roshan. The existing nearby-enemy check (including creeps/summons) and two enemy heroes on high ground veto it while active, with a four-second hold after the last observation. Clock rollback clears an invalid future hold.
- Every positive Roshan offer is at most 0.90, below the current emergency-defense offer of 0.96, including human pings and finishing attempts.
- Visible or recently seen enemies within 2,500 units of the destination pit veto participation (`enemies_near_pit`). Missing enemies are not proof of safety; global living-team parity remains required.
- Readiness counts distinct real allied heroes within 2,500 units of the pit, at least 50% healthy, not retreating, stunned, or disarmed. Illusions, Meepo clones and Tempest Doubles do not inflate the estimate. The evaluating bot must qualify too (`participant_unavailable`). This is a local availability estimate, not a shared commitment or rally system.
- Qualifying allies' damage is summed using seconds per attack. Travel time at current movement speed reduces each ally's contribution over a 60-second window. A 20% allowance covers interruptions. Empty groups cannot qualify. Mana is not counted because the estimate credits right-click damage only.
- Visible Roshan supplies current health, health regeneration and actual incoming physical damage. No speculative armor reduction is added. Without vision, the existing 6,000 + 260/minute health and 30 + 0.375/minute armor estimates remain, with 20 regeneration and standard positive-armor mitigation. Base health/armor/regen were cross-checked against the current d2vpkr unit definitions; growth remains an inherited approximation, not a verified installed-client snapshot.
- Low-health finishing now follows parity, inventory, participant readiness, local danger and pit-change checks. The side-change finishing exception also requires readiness and local/pit safety. It still uses the existing side-change policy, not a calculated kill-before-move guarantee.

Validation: 70 regression tests pass, including participant filtering, additive damage, attack interval, arrival discount, fog-safe estimates, threat expiry and finishing safety. Existing defense regression checks pass. No live match has been run for this revision.

Next playtest: use fixed lobby/FretBots settings and capture Roshan diagnostics. Check that `ancient_danger_or_damage` clears after a defended base becomes safe; inspect `participant_unavailable`, `dps_not_ready` and `enemies_near_pit` for excessive passivity; compare abandoned attempts and isolated deaths with completed kills. The 2,500-unit radius, health cutoff and interruption allowance need gameplay calibration. Travel estimates use straight-line distance and do not establish path reachability or survival under Roshan's attacks.

References: [bot API](https://docs.moddota.com/lua_bots/) for `GetSecondsPerAttack` and `GetActualIncomingDamage`; [extracted unit definitions](https://raw.githubusercontent.com/dotabuff/d2vpkr/master/dota/scripts/npc/npc_units.txt), read October 12, 2026. Earlier notes below are retained as historical context.

Reviewed 2026-09-05, on top of the shared-code repairs recorded in `AUDIT_2026-09-04.md`. This change adds observation, not new objective policy. No matches have been run to measure its gameplay effects.

Updated September 27: the mode now uses the shared pit helper, refreshes readiness on every executed DPS check, and reacquires invalid Roshan handles. These are targeted policy/validity repairs after the original observation-only pass. See [PATCH_REVIEW_2026-09-27.md](PATCH_REVIEW_2026-09-27.md). Live-match verification is still pending.

## What actually chooses the objective

`bots/mode_roshan_generic.lua` supplies `GetDesire()`, which delegates to `GetDesireHelper()`. The engine compares that offer with other modes. This file does not implement `Think()`, `OnStart()`, or `OnEnd()`: its Lua logic does not directly execute a rally, enforce a shared commitment, or measure arrival. A positive desire or a Roshan announcement is therefore not proof that the bot selected or reached the objective.

The logger records `active_mode` alongside the desire for that reason. The mode observed during evaluation can reflect an earlier engine decision; compare consecutive samples. Other ability, movement, and engine behavior still needs in-game observation.

## Decision order

The first applicable return wins. Later checks do not necessarily execute.

| Order | Condition | Reason in the log |
|---|---|---|
| 1 | Bot cannot participate | `ineligible_bot` |
| 2 | Team is judged to be pushing a tier-two tower or high ground | `team_pushing` |
| 3 | Enemies near our Ancient, or Ancient below 80% health | `ancient_danger_or_damage` |
| 4 | A team fight is near the bot and the shared helper's current pit | `nearby_teamfight_day` / `nearby_teamfight_night` |
| 5 | At least two enemies seen within five seconds near the bot | `recent_enemies_near_bot` |
| 6 | Cached visible Roshan handle is valid, below half health, with no recently seen enemies near the bot | `finish_low_health_roshan` |
| 7 | Fewer living allies than enemies anywhere on the map | `outnumbered_alive` |
| 8 | At least two living cores have no empty backpack slot | `core_backpacks_full` |
| 9 | Update respawn estimate, timer, and current DPS readiness; then check imminent pit change | `finish_before_side_change` / `side_change_soon` |
| 10 | Visible enemy near the bot | `visible_enemies_near_bot` |
| 11 | Respawn estimate and current DPS permit participation, plus qualifying human ping | `human_ping` |
| 12 | Same readiness flags permit scaled engine desire | `engine_desire_scaled` |
| 13 | Neither final readiness path passes | `respawn_estimate_not_ready` / `dps_not_ready` |

Normal desire is the engine's `GetRoshanDesire()` multiplied by a factor that rises from 1 to 2 over 150 seconds after the local alive-estimate timer starts, capped at 0.95. Each bot evaluates independently. This is not a team commitment timer.

## Findings to investigate next

1. **Permanent DPS latch repaired September 27.** `initDPSFlag` now takes the current check's value, including false. Early-return paths still have `dps_current=na` because the estimator did not execute in that evaluation; the legacy `dps_latched` field then describes the last executed check. The underlying readiness estimate still needs participant-aware redesign.
2. **DPS is averaged over living allied units rather than summed over available participants.** `J.HasEnoughDPSForRoshan()` accumulates estimated right-click damage, divides by the list length, and compares that average with a 60-second kill threshold. The supplied list has no distance, arrival, health, mana, or commitment filter. Adding a low-damage ally can reduce the estimate. It also has no explicit empty-list guard. Verify attack-speed units and patch-specific armor/health constants before replacing this formula; simply summing the current global list could make bots overconfident.
3. **Pit disagreement repaired September 27.** The nearby-fight gate and trace now both use `J.GetCurrentRoshanLocation()`. Day/night regression checks distinguish the two locations. Their correspondence with the installed map still needs a live check.
4. **Danger is mostly evaluated around the observer.** The 1,200-unit recent-enemy and 1,300-unit visible-enemy gates are centered on the bot, not its intended destination. The trace adds pit-centered observations for comparison. It does not infer safety from missing enemies.
5. **The low-health finish path bypasses later safety/readiness gates.** It precedes living-team parity, backpack capacity, current DPS evaluation, pit-change checks, and the visible-enemy gate. It is not proof of a safe kill window. Check log sequences around interrupted or failed attempts.
6. **Ancient damage creates a persistent veto while health stays below 80%.** This applies without a currently visible attacker. Separate immediate defense from the strategic value of protecting a damaged base when revising policy.
7. **Readiness does not represent a group.** Global living counts and backpack checks do not identify a tank, damage dealers, nearby supports, or an Aegis recipient. The logger's nearby/healthy counts are observations only, not new readiness rules.
8. **Respawn and movement estimates are coarse.** `J.IsRoshanAlive()` uses last-kill time and fixed elapsed thresholds; `J.IsRoshanCloseToChangingSides()` uses the last 30 seconds of a 300-second cycle. Invalid cached Roshan handles are now cleared and reacquired when nearby, as of September 27. Runtime and current-patch validation are required for the timing estimates.
9. **Human ping timing uses mixed clocks.** This mode compares `DotaTime()` with `humanPing.time`; assembly mode uses `GameTime()`. Confirm the timestamp domain in-game before standardizing it. `J.GetHumanPing()` returns the first human teammate's ping rather than searching all humans for the newest one.
10. **Some branches cannot affect the final offer.** The fallback allowing fewer living allies but sufficient DPS is unreachable after the earlier living-team parity return. This is a sign that intent and control flow have diverged.

There is no explicit incoming-teleport, enemy reachable-region, or shared participant-reservation check in this mode. Those are subsequent experiments, not capabilities this change adds. Push code also suppresses some pushing when a bot is doing Roshan and enough allies are near the pit; that interaction should be observed before adding another commitment mechanism.

## Enable the trace

In the effective `Customize/general.lua`, set:

```lua
Customize.Enable = true
Customize.RoshanDiagnostics = true
```

For ordinary local installation this is `bots/Customize/general.lua`. If using permanent customization, set it in `game/Customize/general.lua` in the game's VScript installation instead. The diagnostic switch is read through `J.Customize`, which uses the existing custom loader and respects that override. An older custom file without the option leaves tracing disabled. The TypeScript general-config file is a re-export of this hand-written Lua configuration, not a second settings definition.

Start a fresh local bot match with the updated scripts. Look for `[OHA_ROSHAN]` in the game's console output or a console log captured by your normal setup. Nothing is sent to player chat and no log file is created by these Lua scripts. Set the option back to false and reload the scripts/start a fresh match when finished.

The September 13 repair allows this prefix through the project's global print filter even when `Utils.DebugMode` is false. Earlier versions of this instrumentation were silently suppressed by that filter despite the Roshan switch being enabled.

Sampling is per bot: at most one line every two seconds, with an unchanged-state heartbeat on the first sampled evaluation at least 15 seconds after the previous line. The signature includes reason, active mode, desire in 0.05 buckets, and current/latched DPS. Additional perception queries run only when a line will be emitted. Ten bots can emit at most five lines per second in aggregate under frequent changes. Calls are driven by the engine's mode evaluations, not an independent timer.

## Read the output

Historical illustrative fragment showing the former permanent latch, not a captured match:

```text
[OHA_ROSHAN] t=1200.0 team=2 player=0 reason=engine_desire_scaled desire=0.700 active_mode=7 ... dps_current=false dps_latched=true ... allies=[0@900:82:40:7,1@5400:96:70:1]
```

| Field | Meaning |
|---|---|
| `t`, `team`, `player` | Dota time and the observer's identity; align samples by these fields. |
| `reason`, `desire` | First returned decision reason and the exact offered scalar. |
| `active_mode` | Engine mode ID observed when sampling; not a claim that the current offer won. |
| `pit`, `bot_distance` | Shared helper's destination and observer distance to it. |
| `alive_estimate_cached` | Most recently evaluated respawn estimate; may be stale on early returns. |
| `dps_current` | DPS check from this evaluation, or `na` if skipped. |
| `dps_latched` | Legacy field name retained for log compatibility. Now the latest executed DPS check, including false; may be from an earlier evaluation when `dps_current=na`. |
| `allies_alive` | Living team members observed through team slots. |
| `allies_near2500`, `allies_hp50_near2500` | Members within 2,500 units of the pit; second count additionally requires at least 50% HP. These thresholds are diagnostic only. |
| `enemy_recent_bot1200`, `enemy_recent_pit2500` | Alive enemies whose last-seen records meet the existing helper's under-five-second age and radius limits. Zero does not establish safety. |
| `enemy_visible_pit2500` | Existing helper's visible enemy count near the pit, with that helper's clone/illusion filtering. |
| `allies` | Entries are `playerID@distanceToPit:HPpercent:MPpercent:activeMode`. Humans are included; no intention is assigned to them. |

A change that happens entirely inside the sampling interval may be missed. Unchanged reason/mode/desire/DPS does not trigger a line solely because positions or health changed; the heartbeat will eventually capture them. The trace avoids treating incomplete samples as a full replay.

## First match review

Record script revision, installed game patch, team lineups, game mode, FretBots settings, and whether a human issued pings. Keep resource bonuses constant across comparisons. Review several attempts on both sides, including an uncontested attempt, enemy pressure at the pit, a simultaneous push, and a death or retreat after readiness was first established.

Compare bots' offered desires, their active modes, and actual arrival/death events in the match or replay. Look for positive offers with `dps_current=false`, distant allies counted as readiness, alternating `team_pushing`/Roshan reasons, or safe-looking observer-centered counts while pit-centered counts show danger. The trace cannot itself prove combat success, participant commitment, or unobserved enemy movement.

Pit selection and stale readiness are now repaired. The next implementation should replace the global DPS formula with a bounded, participant-aware estimate, then introduce a rally/abort experiment with explicit required participants. Validate shared-state visibility across bot contexts before assuming one Lua table coordinates the team.

## Verification

Run `python -m unittest discover -s tests -v` as described in `tests/README.md`. The complete suite now has 39 passing tests. The original 16 reason scenarios remain covered; separate cases check current-pit selection, invalid-handle reacquisition, and readiness loss/recovery. Trace checks cover disabled tracing, sampling, unchanged-state heartbeat, per-player isolation, time rollback, and zero maximum mana. Historical stale-latch samples remain supported by the analyzer. Engine mocks cannot establish actual mode scheduling, current map accuracy, or match performance.
