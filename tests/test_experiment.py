import unittest

from src.experiment import required_sample_size, sample_ratio_mismatch, two_proportion_test


class ExperimentTests(unittest.TestCase):
    def test_detects_clear_positive_lift(self):
        result = two_proportion_test(100, 1000, 140, 1000)
        self.assertGreater(result.absolute_lift, 0)
        self.assertTrue(result.significant)
        self.assertLess(result.p_value, 0.05)

    def test_equal_rates_are_not_significant(self):
        result = two_proportion_test(100, 1000, 100, 1000)
        self.assertEqual(result.z_score, 0)
        self.assertFalse(result.significant)

    def test_rejects_empty_variant(self):
        with self.assertRaises(ValueError):
            two_proportion_test(0, 0, 10, 100)

    def test_balanced_assignment_passes_srm(self):
        result = sample_ratio_mismatch(5_000, 5_000)
        self.assertTrue(result["passed"])
        self.assertEqual(result["p_value"], 1.0)

    def test_severe_imbalance_fails_srm(self):
        self.assertFalse(sample_ratio_mismatch(4_000, 6_000)["passed"])

    def test_power_calculation_is_plausible(self):
        size = required_sample_size(0.18, 0.025)
        self.assertGreater(size, 3_000)
        self.assertLess(size, 6_000)


if __name__ == "__main__":
    unittest.main()
