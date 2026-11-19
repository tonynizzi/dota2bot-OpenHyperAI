"""Standard-library tests; no Lua runtime or Dota installation needed."""
import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.analyze_roshan import analyze, classify, main, parse_line, summary


def trace(**changes):
    fields = dict(t="1200.0", team="2", player="0", reason="engine_desire_scaled", desire="0.700",
                  active_mode="7", pit="-100,200", bot_distance="900", alive_estimate_cached="true",
                  dps_current="false", dps_latched="true", allies_alive="3", allies_near2500="1",
                  allies_hp50_near2500="1", enemy_recent_bot1200="0", enemy_recent_pit2500="1",
                  enemy_visible_pit2500="0", allies="[0@900:80:40:7,1@5400:90:70:1,2@6000:60:30:1]")
    fields.update(changes)
    return "[Console] [OHA_ROSHAN] " + " ".join(f"{key}={value}" for key, value in fields.items()) + "\n"


class RoshanAnalyzer(unittest.TestCase):
    def test_parse_current_format_with_prefix_and_unknown_fields(self):
        r = parse_line(trace(future_field="anything"), 4)
        self.assertEqual(r["line"], 4)
        self.assertEqual(r["pit_x"], -100)
        self.assertIs(r["dps_current"], False)
        self.assertEqual(r["allies"][1]["distance"], 5400)
        self.assertEqual(len(classify(r)), 4)

    def test_unknown_readiness_is_not_false_and_zero_offer_is_not_flagged(self):
        self.assertNotIn("stale_dps_offer", classify(parse_line(trace(dps_current="na"), 1)))
        self.assertEqual(classify(parse_line(trace(desire="0"), 1)), [])

    def test_majority_boundary_and_empty_team(self):
        r = parse_line(trace(), 1)
        r["allies_alive"], r["allies_near2500"] = 4, 2
        self.assertNotIn("majority_allies_distant", classify(r))
        r = parse_line(trace(allies_alive="0", allies_near2500="0", allies_hp50_near2500="0", allies="[]"), 1)
        self.assertNotIn("majority_allies_distant", classify(r))

    def test_malformed_records_are_skipped_but_reported(self):
        lines = ["unrelated output\n", trace(), trace(t="nan"), trace(dps_current="unknown"),
                 trace(allies="[broken"), trace().replace(" player=0", ""),
                 trace() + "", trace().rstrip() + " team=3\n", trace(allies_alive="4"),
                 trace(allies_near2500="4")]
        result = analyze(lines)
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["malformed_lines"], 7)
        self.assertEqual(result["ignored_lines"], 1)
        self.assertIn("Line 3", result["warnings"][0])

    def test_rollback_segments_do_not_confuse_interleaved_bots(self):
        result = analyze([trace(t="10"), trace(t="9", player="1"), trace(t="12"),
                          trace(t="-20"), trace(t="-19", player="1")])
        self.assertEqual([r["segment"] for r in result["records"]], [1, 1, 1, 2, 2])
        self.assertIsNone(result["records"][3]["previous_reason"])
        self.assertEqual(len(result["warnings"]), 1)

    def test_changes_long_gaps_and_separate_teams(self):
        result = analyze([trace(t="10"), trace(t="11", team="3"),
                          trace(t="15", reason="team_pushing", active_mode="8"),
                          trace(t="50", reason="dps_not_ready")])
        rows = result["records"]
        self.assertIsNone(rows[1]["previous_reason"])
        self.assertTrue(rows[2]["reason_changed"])
        self.assertTrue(rows[2]["mode_changed"])
        self.assertFalse(rows[2]["long_gap"])
        self.assertTrue(rows[3]["long_gap"])
        self.assertEqual(rows[3]["gap_seconds"], 35)

    def test_cli_utf16_csv_json_and_non_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "console.log"
            log.write_text("Dota console\n" + trace(dps_current="na") + trace(t="1216"), encoding="utf-16")
            output = root / "report"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(log), "--out", str(output), "--notes", "FretBots off"]), 0)
            data = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
            self.assertIsNone(data["records"][0]["dps_current"])
            self.assertEqual(data["notes"], "FretBots off")
            with (output / "timeline.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["dps_current"], "na")
            self.assertEqual(json.loads(rows[1]["allies"])[0]["player"], 0)
            before = (output / "summary.md").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([str(log), "--out", str(output)])
            self.assertEqual((output / "summary.md").read_bytes(), before)

    def test_no_samples_and_bad_options_do_not_write_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "console.log"
            log.write_text("no trace here", encoding="utf-8")
            for options in ([], ["--max-gap", "nan"], ["--max-gap", "0"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main([str(log), "--out", str(root / "report"), *options])
            self.assertFalse((root / "report").exists())

    def test_summary_preserves_sample_caveats_and_source_lines(self):
        result = summary(analyze([trace(), trace(t="1216", reason="team_pushing", desire="0")]), "synthetic.log", "test data")
        self.assertIn("sample percentages are not time percentages", result)
        self.assertIn("stale_dps_offer | 1", result)
        self.assertIn("20:00.0", result)
        self.assertIn("Source line", result)


if __name__ == "__main__":
    unittest.main()
