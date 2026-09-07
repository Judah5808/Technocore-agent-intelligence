import unittest

from monitor import classify_message


class TestClassifyMessage(unittest.TestCase):
    def test_testnet_message_is_high_signal(self):
        category, score, signals = classify_message(
            "batch ready for the FLOP Labs testnet"
        )

        self.assertEqual(category, "high")
        self.assertGreaterEqual(score, 4)
        self.assertTrue(signals)

    def test_security_message_is_high_signal(self):
        category, score, signals = classify_message(
            "security vulnerability discovered in the API"
        )

        self.assertEqual(category, "high")
        self.assertGreaterEqual(score, 4)
        self.assertTrue(signals)

    def test_simple_message_is_low_signal(self):
        category, score, signals = classify_message(
            "hello everyone"
        )

        self.assertEqual(category, "low")
        self.assertEqual(score, 0)
        self.assertEqual(signals, [])


if __name__ == "__main__":
    unittest.main()
