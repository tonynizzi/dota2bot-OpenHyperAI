"""Analyze sampled OHA Roshan console lines. Python standard library only."""
import argparse
from collections import Counter, defaultdict
import csv
import io
import json
import math
from pathlib import Path
import re
import sys

MARKER = "[OHA_ROSHAN]"
INT_FIELDS = ("team", "player", "active_mode", "allies_alive", "allies_near2500",
              "allies_hp50_near2500", "enemy_recent_bot1200", "enemy_recent_pit2500",
              "enemy_visible_pit2500")
FLOAT_FIELDS = ("t", "desire", "bot_distance")
BOOL_FIELDS = ("alive_estimate_cached", "dps_current", "dps_latched")
FLAG_DESCRIPTIONS = {
    "stale_dps_offer": "Positive desire with dps_current=false and dps_latched=true.",
    "majority_allies_distant": "Positive desire with more than half of living allies outside 2,500 units of the pit.",
    "few_healthy_nearby": "Positive desire with fewer than two allies at >=50% HP within 2,500 units (includes the observer).",
    "pit_enemy_signal": "Positive desire, no recent enemies near the bot, but recent or visible enemies near the pit. Radii differ; this is a review signal, not proof of danger.",
}


def finite(text):
    result = float(text)
    if not math.isfinite(result):
        raise ValueError("non-finite number")
    return result


def parse_line(line, number):
    if MARKER not in line:
        return None
    payload = line.split(MARKER, 1)[1]
    pairs = re.findall(r"(\w+)=(\[[^\]]*\]|[^\s]+)", payload)
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("duplicate field")
    required = set(INT_FIELDS + FLOAT_FIELDS + BOOL_FIELDS + ("reason", "pit", "allies"))
    missing = required - fields.keys()
    if missing:
        raise ValueError("missing fields: " + ", ".join(sorted(missing)))
    record = {"line": number, "reason": fields["reason"]}
    if not re.fullmatch(r"[A-Za-z0-9_]+", record["reason"]):
        raise ValueError("invalid reason")
    for key in INT_FIELDS:
        record[key] = int(fields[key])
        if record[key] < 0:
            raise ValueError(f"negative {key}")
    for key in FLOAT_FIELDS:
        record[key] = finite(fields[key])
    if record["bot_distance"] < 0 or record["desire"] < 0:
        raise ValueError("negative distance/desire")
    for key in BOOL_FIELDS:
        if fields[key] not in ("true", "false", "na"):
            raise ValueError(f"invalid boolean {key}")
        record[key] = {"true": True, "false": False, "na": None}[fields[key]]
    pit = fields["pit"].split(",")
    if len(pit) != 2:
        raise ValueError("invalid pit coordinates")
    record["pit_x"], record["pit_y"] = map(finite, pit)
    if not (fields["allies"].startswith("[") and fields["allies"].endswith("]")):
        raise ValueError("incomplete allies list")
    allies = []
    for entry in filter(None, fields["allies"][1:-1].split(",")):
        match = re.fullmatch(r"(\d+)@([\d.]+):([\d.]+):([\d.]+):(\d+)", entry)
        if not match:
            raise ValueError("invalid ally entry")
        player, distance, hp, mp, mode = match.groups()
        allies.append(dict(player=int(player), distance=finite(distance),
                           hp_percent=finite(hp), mp_percent=finite(mp), active_mode=int(mode)))
    if len({ally["player"] for ally in allies}) != len(allies):
        raise ValueError("duplicate ally ID")
    if len(allies) != record["allies_alive"]:
        raise ValueError("allies list/count mismatch")
    if not (record["allies_hp50_near2500"] <= record["allies_near2500"] <= record["allies_alive"]):
        raise ValueError("inconsistent ally counts")
    record["allies"] = allies
    return record


def classify(record):
    flags = []
    if record["desire"] <= 0:
        return flags
    if record["dps_current"] is False and record["dps_latched"] is True:
        flags.append("stale_dps_offer")
    if record["allies_near2500"] * 2 < record["allies_alive"]:
        flags.append("majority_allies_distant")
    if record["allies_hp50_near2500"] < 2:
        flags.append("few_healthy_nearby")
    if record["enemy_recent_bot1200"] == 0 and (
        record["enemy_recent_pit2500"] > 0 or record["enemy_visible_pit2500"] > 0
    ):
        flags.append("pit_enemy_signal")
    return flags


def analyze(lines, max_gap=20):
    records, warnings = [], []
    malformed, ignored, session = 0, 0, 1
    previous = {}
    for number, line in enumerate(lines, 1):
        try:
            record = parse_line(line, number)
        except ValueError as error:
            malformed += 1
            if len(warnings) < 100:
                warnings.append(f"Line {number}: {error}")
            continue
        if record is None:
            ignored += 1
            continue
        key = record["team"], record["player"]
        old = previous.get(key)
        # Only compare an observer with itself: interleaved bots may arrive out of order.
        if old and record["t"] < old["t"]:
            session += 1
            previous.clear()
            old = None
            if len(warnings) < 100:
                warnings.append(f"Line {number}: observer time moved backward; started segment {session}. This may be a new match or reordered output.")
        record["segment"] = session
        record["gap_seconds"] = None if old is None else round(record["t"] - old["t"], 3)
        record["previous_reason"] = None if old is None else old["reason"]
        record["reason_changed"] = old is not None and old["reason"] != record["reason"]
        record["mode_changed"] = old is not None and old["active_mode"] != record["active_mode"]
        record["long_gap"] = old is not None and record["gap_seconds"] > max_gap
        record["flags"] = classify(record)
        records.append(record)
        previous[key] = record
    return {"records": records, "warnings": warnings, "malformed_lines": malformed,
            "ignored_lines": ignored, "max_gap_seconds": max_gap}


def clock(seconds):
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    return f"{sign}{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def summary(data, name, notes):
    records = data["records"]
    groups = defaultdict(list)
    for record in records:
        groups[record["segment"], record["team"], record["player"]].append(record)
    flags = Counter(flag for record in records for flag in record["flags"])
    out = ["# Roshan log analysis", "", f"Input: {name}", ""]
    if notes:
        out.extend(["Match notes: " + notes.replace("\n", " "), ""])
    out.extend([
        f"Parsed **{len(records)} samples**; skipped {data['malformed_lines']} malformed trace lines and {data['ignored_lines']} unrelated lines.",
        "", "Counts describe sampled observations, not time spent, committed attempts, or successful kills. Logs favor state changes and also contain heartbeats, so sample percentages are not time percentages.",
        "", "## Review signals", "", "| Signal | Samples |", "|---|---:|",
    ])
    for flag in FLAG_DESCRIPTIONS:
        out.append(f"| {flag} | {flags[flag]} |")
    out.extend(["", *[f"- **{key}**: {value}" for key, value in FLAG_DESCRIPTIONS.items()]])
    out.extend(["", "## Bot summary", "", "| Segment | Team | Player | First–last sample | Samples | Positive offers | Reason changes | Mode changes | Long gaps |",
                "|---:|---:|---:|---|---:|---:|---:|---:|---:|"])
    for (segment, team, player), rows in sorted(groups.items()):
        out.append(f"| {segment} | {team} | {player} | {clock(rows[0]['t'])}–{clock(rows[-1]['t'])} | {len(rows)} | "
                   f"{sum(r['desire'] > 0 for r in rows)} | {sum(r['reason_changed'] for r in rows)} | "
                   f"{sum(r['mode_changed'] for r in rows)} | {sum(r['long_gap'] for r in rows)} |")
    out.extend(["", f"Changes compare consecutive observations of the same bot. Gaps over {data['max_gap_seconds']:g}s are marked; no continuous behavior is inferred across them. Mode IDs are preserved as emitted, not guessed. A desire offer does not establish that Roshan mode won.",
                "", "## Decision reasons", "", "| Reason | Samples |", "|---|---:|"])
    for reason, count in Counter(r["reason"] for r in records).most_common():
        out.append(f"| {reason} | {count} |")
    out.extend(["", "## Timeline highlights", "", "First 100 flagged samples or observed reason/mode changes, ordered by segment and game time. Full data is in timeline.csv and analysis.json.", "",
                "| Segment | Time | Team/player | Reason | Desire | Mode | Flags / change | Source line |",
                "|---:|---|---|---|---:|---:|---|---:|"])
    highlights = [r for r in records if r["flags"] or r["reason_changed"] or r["mode_changed"]]
    for r in sorted(highlights, key=lambda r: (r["segment"], r["t"], r["line"]))[:100]:
        labels = r["flags"] + (["reason changed"] if r["reason_changed"] else []) + (["mode changed"] if r["mode_changed"] else []) + (["long gap"] if r["long_gap"] else [])
        out.append(f"| {r['segment']} | {clock(r['t'])} | {r['team']}/{r['player']} | {r['reason']} | {r['desire']:.3f} | {r['active_mode']} | {', '.join(labels)} | {r['line']} |")
    if data["warnings"]:
        out.extend(["", "## Input warnings", "", *["- " + warning for warning in data["warnings"]]])
    out.extend(["", "Time rollback segments are heuristic, not match IDs. Analyze one match per file where possible. Missing sightings do not establish safety; bot-centered and pit-centered query radii differ. Nothing here estimates win rate, kill outcome, fog positions, or unsampled transitions.", ""])
    return "\n".join(out)


def write_reports(data, directory, name, notes):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "summary.md").write_text(summary(data, name, notes), encoding="utf-8")
    payload = dict(data, input=name, notes=notes, flag_definitions=FLAG_DESCRIPTIONS)
    (directory / "analysis.json").write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    columns = ["segment", "line", "t", "team", "player", "reason", "desire", "active_mode",
               "previous_reason", "reason_changed", "mode_changed", "gap_seconds", "long_gap",
               "dps_current", "dps_latched", "alive_estimate_cached", "pit_x", "pit_y", "bot_distance",
               "allies_alive", "allies_near2500", "allies_hp50_near2500", "enemy_recent_bot1200",
               "enemy_recent_pit2500", "enemy_visible_pit2500", "flags", "allies"]
    with (directory / "timeline.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in sorted(data["records"], key=lambda r: (r["segment"], r["t"], r["line"])):
            row = dict(record, flags=";".join(record["flags"]), allies=json.dumps(record["allies"]))
            for key in BOOL_FIELDS:
                row[key] = "na" if row[key] is None else str(row[key]).lower()
            writer.writerow(row)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Console log containing [OHA_ROSHAN] lines")
    parser.add_argument("--out", type=Path, help="New or empty output directory (default: next to input, <stem>-roshan)")
    parser.add_argument("--notes", default="", help="Patch, lineup, FretBots state, and other match context")
    parser.add_argument("--max-gap", type=float, default=20, help="Mark observation gaps longer than this many seconds")
    args = parser.parse_args(argv)
    if not math.isfinite(args.max_gap) or args.max_gap <= 0:
        parser.error("--max-gap must be finite and positive")
    output = args.out or args.log.with_name(args.log.stem + "-roshan")
    try:
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            parser.error("output must be a new or empty directory; existing reports are not overwritten")
        with args.log.open("rb") as raw:
            prefix = raw.read(4)
            raw.seek(0)
            encoding = "utf-16" if prefix.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            with io.TextIOWrapper(raw, encoding=encoding, errors="replace") as handle:
                data = analyze(handle, args.max_gap)
        if not data["records"]:
            parser.error(f"no valid Roshan samples found ({data['malformed_lines']} malformed trace lines); no report written")
        write_reports(data, output, str(args.log.resolve()), args.notes)
    except (OSError, UnicodeError) as error:
        parser.error(str(error))
    print(f"Read {len(data['records'])} samples; {data['malformed_lines']} malformed. Report: {(output / 'summary.md').resolve()}")
    if data["malformed_lines"]:
        print("Some trace lines were skipped; see input warnings in the report.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
