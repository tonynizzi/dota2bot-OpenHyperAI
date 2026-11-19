# Combat reaction delay

The local configuration enables a random 150–300 ms response window for new combat cues. This aims to reduce instant spell/item counterplay while allowing existing movement, attacks, channels, and queued actions to continue. It is an initial gameplay tuning setting, not a measured model of human reaction times.

## Configuration

In the effective `Customize/general.lua`:

```lua
Customize.Enable = true
Customize.ReactionDelay = {
    Enable = true,
    MinSeconds = 0.15,
    MaxSeconds = 0.30,
}
```

Use `bots/Customize/general.lua` for local scripts. If permanent customization is installed, add the same block to `game/Customize/general.lua`: an older override without `ReactionDelay` leaves the feature disabled. Start a fresh match after changing configuration. Set the nested `Enable` to false to restore the previous behavior; setting both durations to zero also disables it.

Values are seconds. Invalid/missing durations use 0.15/0.30; each is bounded to 0–1 second and the maximum cannot be below the minimum. Both teams use the same configured range, with a separate random sample for each bot's response window.

## What starts a wait

The shared spell/item decision gate samples the bot's available observations at most once every 50 ms:

- A newly visible enemy hero within 1,600 units, or one returning after a visibility gap longer than 0.5 seconds. Short visibility flickers do not repeatedly delay the bot.
- A nearby visible enemy beginning a cast/channel, or switching the active ability.
- A newly observed incoming non-attack tracking projectile. Friendly projectiles are excluded when their caster is identifiable; ordinary attack projectiles do not trigger a wait. Concurrent spell counts use caster/ability identity because the API does not supply a stable projectile ID.
- The start of a fresh recent-hero-damage interval. A continuously true damage signal does not restart the timer on every tick.

The random deadline is sampled once for the burst. Additional cues during that wait are observed but cannot extend it indefinitely. When it expires, both ability and item callbacks get a brief shared reconsideration window. Later distinct cues can start another wait. A cue near the end of a pending burst therefore does not receive a separate full delay.

The deadline runs from observation, not from the exact engine event. The existing callback cadence, scan interval, and `ThinkLess` setting can add time. The configured 150–300 ms range is the sampled waiting window, not a guarantee that every observed response lands inside that wall-clock range.

## Scope and safeguards

The gate runs before `BotBuild.SkillsComplement()` and `ItemUsageComplement()` in `ability_item_usage_generic.lua`, using the effective `J.Customize` settings. While waiting, it skips the new decision pass rather than storing a target/order or inserting `Action_Delay`. When ready, the existing decision code rechecks targets, range, resources, and threats. A vanished target is not acted on from a stored command.

No action is cleared or canceled. Previously issued attacks, movement, channels, and queued combos continue. There is no blanket per-action delay. Purchases, leveling, courier, and buyback callbacks are unchanged. Decisions made directly by other modes, minion controllers, or Valve's engine are not covered; this is not a universal reaction floor for every bot action. It also does not detect every ground effect or non-tracking projectile.

State is per bot handle, resets on death, clock rollback, or disable, and is discarded with the handle. Visible enemies are checked before reading their cast state. Disabled settings perform no additional perception scans. Enabled scanning adds nearby-hero/projectile queries; its live performance cost has not been measured.

## Validation and next match

All 50 regression tests pass. Eleven reaction tests cover deadlines, independent jitter, shared ability/item timing, sustained casts, bursts, fog and flicker, projectile identity, damage signals, disabled/invalid settings, lifecycle resets, and production callbacks reevaluating a changed target. Existing diagnostics and maintenance tests also pass.

No live match has been run with this change. Compare enabled/disabled games with the same `ThinkLess`, FretBots bonuses, and lobby settings. Check Anti-Mage Counterspell, Puck Phase Shift, instant disables when blinking into vision, and defensive item use. Also check that farming and already queued combinations continue normally. Retain examples of remaining instant reactions with the hero and action involved; they may originate in an uncovered mode or the engine.

The bot API reference for visible-unit observations and incoming projectiles is [ModDota's bot API](https://docs.moddota.com/lua_bots/).
