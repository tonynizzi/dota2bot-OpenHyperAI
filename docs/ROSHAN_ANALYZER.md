# Analyze a Roshan console log

This offline tool reads the diagnostic lines described in `ROSHAN_DECISIONS.md`. It does not connect to Dota, change scripts, or modify the input log. Python's standard library is sufficient; no package installation is needed.

From the project root, run (replace the example input with your saved log):

```powershell
python tools/analyze_roshan.py 'C:\path\to\console.log' --out 'temp_build\playtest-01' --notes 'FretBots off; record patch, lineup, and notable match times here'
```

If Python is not on PATH, the runtime available in this workspace can run the same command:

```powershell
& 'C:\Users\tonyn\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/analyze_roshan.py 'C:\path\to\console.log' --out 'temp_build\playtest-01' --notes 'FretBots off'
```

Use a new output directory for each run. Existing reports are not overwritten. Omitting `--out` creates `<input-stem>-roshan` beside the log. The console prints the report location when complete. The tool does not enable or capture engine logging itself; save your console output first.

## Outputs

| File | Use |
|---|---|
| `summary.md` | Signal counts, per-bot sample spans, observed reason/mode changes, and up to 100 timeline highlights. |
| `timeline.csv` | Every valid sample ordered by segment and game time, with original source line, gap, flags, and ally observations. Can be opened in a spreadsheet. |
| `analysis.json` | Complete parsed observations, notes, flag definitions, parse warnings, and unknown readiness as JSON null. |

Review signals are deliberately simple:

- **stale_dps_offer:** desire above zero despite a failed current DPS check and a true latch.
- **majority_allies_distant:** desire above zero while more than half the living allies are outside 2,500 units of the pit.
- **few_healthy_nearby:** desire above zero with fewer than two living allies at >=50% HP within 2,500 units. Includes the observer and humans; this is not a recommended minimum team size.
- **pit_enemy_signal:** desire above zero with no recent bot-centered sightings, but recent or visible pit-centered sightings. Different query centers and radii mean this is a discrepancy to inspect, not proof of a bad decision.

`na` readiness is kept distinct from false. Mode IDs remain numeric as emitted; the analyzer does not assume that an offered Roshan desire won mode selection. Reason and mode changes compare consecutive samples from the same team/player. A gap over 20 seconds is marked `long_gap`; adjust with `--max-gap 30` if needed. These comparisons do not establish what happened inside the gap.

The September 27 readiness repair retains the `dps_latched` field for compatibility but updates it to false when the current check fails. The `stale_dps_offer` signal remains useful for historical logs and detecting old/mixed installations; it is not expected from the repaired ordinary readiness path. Cast-attempt lines prefixed `[OHA_CAST]` are ignored by this Roshan-only analyzer; inspect those alongside the engine messages as described in `ACTION_DIAGNOSTICS.md`.

## Input handling and limits

Mixed console output and prefixes before `[OHA_ROSHAN]` are accepted. UTF-8 (with or without BOM) and BOM-marked UTF-16 logs are supported. Malformed/truncated trace lines are skipped and counted; up to 100 warning details are retained. A file with no valid samples produces an error and no report. Additional future fields are ignored; the fields in the current diagnostic format are required.

If time moves backward for an already observed bot, the tool starts another segment and resets comparison state. This may indicate another match or reordered output; it is not a reliable match identifier. Prefer one match per input file. Repeated lines are retained, so concatenating overlapping captures can inflate counts. Capture a completed copy of the log for repeatable analysis.

Sampling favors state changes and includes intermittent heartbeats. Counts are **sample counts**, not time percentages, attempt counts, or win rates. The first/last timestamp is an observation span, not a duration of commitment. Unseen enemies are not inferred, nearby allies are not assumed to cooperate, and kills/arrival/deaths must be correlated with observations or a replay. No actual match is bundled with the tool; all test inputs are synthetic.

Run the analyzer's tests independently of the Lua tests:

```powershell
python -m unittest discover -s tests -p test_roshan_analyzer.py -v
```
