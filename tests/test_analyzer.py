import unittest

from analyzer import (
    build_activity_summary,
    build_agent_profiles,
    build_report,
    build_signal_summary,
    signal_names_from_text,
)


class TestAnalyzer(unittest.TestCase):
    def test_signal_names_are_detected(self):
        signals = signal_names_from_text(
            "I found a security vulnerability in the API"
        )

        self.assertIn("security", signals)
        self.assertIn("vulnerability", signals)
        self.assertIn("api", signals)

    def test_agent_profiles_group_messages_by_did(self):
        records = [
            {
                "seq": 1,
                "ts": "2026-09-06T10:00:00Z",
                "from": "did:key:zTestAgent",
                "text": "testnet deployment is ready",
                "category": "high",
                "score": 5,
                "signals": ["testnet"],
            },
            {
                "seq": 2,
                "ts": "2026-09-06T10:05:00Z",
                "from": "did:key:zTestAgent",
                "text": "API documentation update",
                "category": "medium",
                "score": 2,
                "signals": ["api", "documentation"],
            },
        ]

        profiles = build_agent_profiles(records)

        self.assertEqual(len(profiles), 1)

        profile = profiles[0]

        self.assertEqual(profile["did"], "did:key:zTestAgent")
        self.assertEqual(profile["messages"], 2)
        self.assertEqual(profile["high_signal"], 1)
        self.assertEqual(profile["medium_signal"], 1)
        self.assertEqual(profile["low_signal"], 0)
        self.assertEqual(profile["total_score"], 7)

    def test_signal_summary_counts_signals(self):
        records = [
            {
                "text": "testnet API is ready",
            },
            {
                "text": "testnet deployment is ready",
            },
        ]

        summary = build_signal_summary(records)

        self.assertEqual(summary["testnet"], 2)
        self.assertEqual(summary["api"], 1)


class TestActivitySummary(unittest.TestCase):
    def test_activity_summary_counts_categories_and_average(self):
        records = [
            {"category": "high", "score": 5},
            {"category": "medium", "score": 3},
            {"category": "low", "score": 1},
        ]

        summary = build_activity_summary(records)

        self.assertEqual(summary["high_signal"], 1)
        self.assertEqual(summary["medium_signal"], 1)
        self.assertEqual(summary["low_signal"], 1)
        self.assertEqual(summary["average_score"], 3.0)


class TestBuildReport(unittest.TestCase):
    def test_build_report_contains_expected_sections(self):
        records = [
            {
                "seq": 100,
                "ts": "2026-09-07T10:00:00Z",
                "from": "did:key:zTestAgent",
                "text": "FLOP Labs testnet deployment is ready",
                "category": "high",
                "score": 5,
            },
            {
                "seq": 101,
                "ts": "2026-09-07T10:01:00Z",
                "from": "did:key:zOtherAgent",
                "text": "API documentation update",
                "category": "medium",
                "score": 2,
            },
        ]

        report = build_report(records)

        self.assertIn("summary", report)
        self.assertIn("signal_summary", report)
        self.assertIn("agent_profiles", report)
        self.assertIn("noteworthy_activity", report)

        self.assertEqual(report["summary"]["high_signal"], 1)
        self.assertEqual(report["summary"]["medium_signal"], 1)
        self.assertEqual(report["summary"]["low_signal"], 0)
        self.assertEqual(report["summary"]["average_score"], 3.5)
        self.assertEqual(len(report["agent_profiles"]), 2)


if __name__ == "__main__":
    unittest.main()
