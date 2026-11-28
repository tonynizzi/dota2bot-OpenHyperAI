# Cast-attempt diagnostics

Added September 27, 2026. These opt-in observations identify which script, hero, ability/item, order method, and target type were involved in sampled cast attempts. They do not intercept engine rejection messages or prove that an order executed successfully.

## Enable for a short playtest

In the effective `Customize/general.lua`, set:

```lua
Customize.Enable = true
Customize.ActionDiagnostics = true
Customize.DiagnosticsGamePatch = '7.41f' -- Replace with the patch shown by your installed client.
```

Use `bots/Customize/general.lua` for ordinary local scripts, or `game/Customize/general.lua` when permanent customization is installed. Older custom files without these settings leave cast tracing off. The default patch label is `unknown`; no installed patch is inferred from the patch we reviewed.

Start a fresh Local Dev Script match. Look for `[OHA_CAST]` in the console or your saved console log. Global debug mode is not required. The scripts do not write a separate log file or send chat messages. Turn `ActionDiagnostics` off and restart the match after collecting the sample. Existing Roshan tracing has a separate switch.

## Reading the output

The first observed attempt per player/controlled-unit name emits an `event=session` header with:

- `script_revision=maintenance-2026-09-27`: the diagnostic code's maintenance revision label, not a Git commit or Workshop release version.
- `script_path`: the loaded script directory. Spaces are escaped as underscores.
- `game_patch` and `patch_source=user_config`: the patch label entered above, not an automatic detection.
- `player` and `hero`: the controlled unit submitting the order. Shared player/name combinations, such as some clones, share a rate limit.

Sampled `event=attempt` records contain game time, player, hero, action method, ability/item name, target type, visible target name (or `unseen_or_invalid`), live behavior flags, item inventory slot, warning, and the number of attempts omitted since the previous sample in that category.

Warnings are diagnostic hints:

| Warning | Meaning |
|---|---|
| `target_type_mismatch` | The requested unit/point/no-target order disagrees with the inspected behavior flags. Hybrid abilities and engine exceptions still require review. |
| `inactive_inventory_slot` | The item is in slots 6–14 (backpack/stash) when the order is submitted. Queued inventory changes may occur before execution. |
| `hidden_ability` / `nil_ability` | The submitted ability is hidden or missing. Existing action guards may already block it. |
| `none` | No checked mismatch was found; this is not an assertion that the cast is legal or succeeded. |

For Bounty Hunter's Shuriken, `shuriken_damage` records the live `bonus_damage` special value and `damage_talent_trained` checks the damage talent by name. In an unmodified 7.41f client, inspect rank-four readings before and after taking the +190 damage talent: the expected talent-inclusive values are 310 and 500. This is a runtime API verification task, not something the mocked tests establish. If the trained reading stays at 310, retain that log and compare against actual spell damage before introducing a talent-aware fallback.

## Sampling and safeguards

At most one normal attempt and one suspect attempt are printed every two seconds per player/unit-name pair, plus the session header. Ordinary casts cannot consume the suspect sample allowance. A backwards game clock resets that pair's session. This sampling can miss individual casts and is not a full action history.

The wrappers cover immediate, queued, and pushed no-target, unit, point, and tree cast orders. They preserve the original arguments, returns, and errors. Diagnostic failures are contained so they cannot prevent the original call. Disabled tracing does not inspect handles. Enemy target names are only queried when visible. The diagnostic module does not issue actions.

The session header identifies the diagnostic module present in that installation; it cannot prove that every other file was copied correctly. Keep a record of the copied working-tree snapshot/commit, client build, lineups, lobby mode, and FretBots settings with the logs. The older `error in error handling` messages are still unattributed; this trace improves correlation, not stack-trace recovery.

## Verification

`python -m unittest discover -s tests -v` exercises all 12 order methods, argument/return preservation, original-error propagation, duplicate-install protection, disabled behavior, independent rate limits, clock rollback, stash warnings, fog handling, Shuriken values, logger failure, and the real global print/hidden-ability guards.
