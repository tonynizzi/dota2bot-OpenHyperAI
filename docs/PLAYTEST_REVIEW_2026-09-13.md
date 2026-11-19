# Saved playtest review, September 13, 2026

Reviewed the five session logs for September 6 (morning and afternoon), 7, 9, and 10. Archived source files and replay copies are under `temp_build/playthrough-recovery-20260913-181709`. Replays have not been played back or decoded. Log attribution remains incomplete: rejected orders identify account 0 without a hero, item, or ability name.

## Evidence and repairs

- September 6 afternoon: 786 rejected orders saying an ability cannot be cast with a target. Bristleback's Goo always used the entity-target command. Dispatch now checks the live no-target behavior flag, retaining entity targeting otherwise. This supports a changed ability configuration without assuming a particular patch or upgrade. It is not proven to be the source of these 786 messages.
- September 10: 33 rejected orders saying an ability cannot be cast with a position. Lion inferred point-target Hex from the eighth talent slot. Both target selection and command dispatch now use Hex's live point-target flag. The log does not establish Lion as the source of the September 10 errors; this is a code-level repair to the same class of failure.
- September 7: 422 rejected stash-item orders. Ward mode retained handles across inventory scans and did not revalidate inventory location before using them. It now clears the previous plan on each evaluation and verifies the actual ward handle remains in slots 0–5 before moving to plant or casting. This also handles inventory changes between evaluation and action. Other stash-item sources remain possible.
- Ward mode could retain an observer handle while selecting a sentry destination, then prioritize the observer during execution. That handle is now cleared before considering sentry placement. Core heroes also return numeric zero desire instead of boolean false.
- No Roshan samples were present. The global `print` override suppressed our opt-in trace whenever `Utils.DebugMode` was false. The override now permits the `[OHA_ROSHAN] ` prefix independently of debug mode. The existing Roshan configuration gates and rate limits still control emission. This omission in our original instrumentation explains how tracing could be enabled yet absent; it does not independently prove which installation ran each match.

The bot API documents `GetBehavior()` and distinct no-target, unit-target, and location-target action methods: https://docs.moddota.com/lua_bots/. The changes use the project's existing behavior-bit helper rather than hardcoded patch metadata.

## Validation and limits

Six new Lua 5.1 regression tests exercise the production print filter, ward selection/execution across inventory changes, sentry selection with an observer in inventory, numeric core desire, Lion target construction and dispatch, and Bristleback dispatch in both behavior configurations. The complete 27-test suite passes with mocked engine APIs. Live-match validation is still required.

Each session contains exactly 20 `Script Runtime Error: error in error handling` messages without useful stack traces. These remain unresolved; neither the responsible code nor a reporting cap has been established. September 10 also contains individual GetDesire timings of 35.097 ms (Ogre Magi) and 17.431 ms (Medusa), which justify profiling but not an unmeasured policy or caching change.

Before a full match, verify that a short Local Dev Script session produces saved Roshan samples with RoshanDiagnostics enabled and global debug disabled. Keep FretBots and lobby settings consistent. Compare rejected-order categories in the next log, and correlate lingering failures with the replay before attributing changes in coordination or win rate.
