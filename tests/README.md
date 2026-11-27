# Bot regression checks

These tests execute shipped Lua with Lupa's Lua 5.1 runtime and small Dota API mocks. They cover team indexing on both sides, clone filtering, mixed unit enumeration, target lock callers, cache expiry, Roshan scoring, ping lifetime, modified-Lua syntax, and the Node post-processor's failure status. They do not launch Dota or establish improved win rates.

Requires Python 3.12 (a compatible Lupa wheel), Node.js, and Git for baseline comparisons. From the project root:

```powershell
python -m pip install --target temp_build/python-deps lupa==2.6
python -m unittest discover -s tests -v
```

The test loader also accepts Lupa installed in the active Python environment. Use your Python executable's full path if it is not on PATH.

The Roshan diagnostics follow-up adds three tests (including 16 decision-branch scenarios), bringing the suite to twelve. See `docs/ROSHAN_DECISIONS.md` for the tracing switch and log interpretation.

The offline analyzer adds nine standard-library tests, bringing the complete suite to 21. To test only the analyzer without installing Lupa, run `python -m unittest discover -s tests -p test_roshan_analyzer.py -v`. The diagnostics suite also verifies that the analyzer accepts output from the actual Lua emitter. Usage: `docs/ROSHAN_ANALYZER.md`.

The September 13 playtest repairs add six regression tests, bringing the suite to 27. They cover tracing through the global print filter, ward inventory changes and ward-type selection, numeric ward desire, and behavior-dependent Hex/Goo targeting. See `docs/PLAYTEST_REVIEW_2026-09-13.md` for evidence and remaining limits.

The September 27 maintenance adds twelve tests, bringing the suite to 39. They cover Treant unit-target decisions/dispatch, range and disarm/castability checks, Bounty Hunter's live damage without a talent-slot addition, day/night Roshan pit consistency, invalid-handle reacquisition, and passive cast diagnostics. The existing readiness test now verifies loss and recovery. See `docs/PATCH_REVIEW_2026-09-27.md` and `docs/ACTION_DIAGNOSTICS.md`. Talent-inclusive engine special values still need in-game verification.

The reaction-delay follow-up adds eleven tests, bringing the complete suite to 50. These exercise the shared spell/item gate, new-cue detection, sampled deadlines, burst handling, visibility, projectile counts, fresh damage, lifecycle resets, configuration bounds, and production callback integration. See `docs/REACTION_DELAY.md` for the enabled 150–300 ms setting and the limits of its coverage.

The local update-notice follow-up adds eight tests, bringing the complete suite to 58. These check the two chat lines, timing, a single elected bot across isolated contexts, Dire player IDs, clone/death suppression, disable options, accurate settings text, clock reset, and the production hook. See `docs/LOCAL_UPDATE_NOTICE.md` for the local release metadata and mute switch.

To demonstrate the defects against the original commit in PowerShell:

```powershell
$env:OHA_TEST_REVISION = 'cb814c6c8dc51ed08045d6efd9f4a48147992711'
python -m unittest discover -s tests -p test_bot_regressions.py -v
Remove-Item Env:OHA_TEST_REVISION
```

Lua assertions appear as unittest errors on the defective baseline. The baseline should fail the eight behavioral/tooling checks; its syntax check passes.

To compile without overwriting unrelated shipped files:

```powershell
npm ci --ignore-scripts --legacy-peer-deps
node node_modules/typescript-to-lua/dist/tstl.js -p tsconfig-tstl.json --outDir temp_build/generated
node typescript/post-process/post-process-lua.js temp_build/generated/bots
```

The compatibility flag is needed for the existing lockfile: TypeScript is 5.5.4 while TSTL 1.26.2 declares a 5.5.2 peer. It does not fix that upstream dependency mismatch. The audited build passes with four existing truthiness warnings in `advanced_item_strategy.ts`. Compare generated files before copying the affected output into `bots`; do not include unrelated generated drift. `npm run build:lua` retains the normal full build behavior. The existing `npm run dev` watcher still does not run post-processing; use the full build before testing in-game.

The 7.42 compatibility pass adds eleven tests in `test_patch_742.py`, bringing the suite to 81. They check that removed abilities (MegaMeepo, Swiftslash, Summon Convert) and removed items (Khanda, Helm of the Overlord, Javelin) are no longer referenced, that new 7.42 items expand into components, that both neutral tables match the 7.42 four-tier pools, the 7.42 XP tables, the shrinking Roshan respawn window, and the Invoker skill list with its three bonus orb points. See `docs/PATCH_REVIEW_2026-11-18.md`.

The Watcher capture follow-up adds eight tests in `test_watcher_capture.py`, bringing the suite to 89. They load the shipped `mode_watcher_generic.lua` override with engine mocks and check that a support walks to and channels `ability_lamp_use` on a nearby neutral Watcher, does not re-target one it lit, turns off enemy Watchers, backs off after a cast that never channels, ignores Watchers when enemies are near, when retreating, fighting, low or already owning it, keeps cores on short detours only, that the `[OHA_WATCHER]` trace passes the print filter, that the engine Watcher mode is overridden while the outpost mode is untouched, and that farm mode still filters Watchers out. See `docs/WATCHER_CAPTURE.md`.

In-game follow-up: check both Radiant and Dire pushing/Roshan decisions, Bounty Hunter bounce candidates, Arc Warden unit counts, target changes when allies need help, and repeated/interrupted human pings. Hold FretBots bonuses constant when comparing gameplay.
