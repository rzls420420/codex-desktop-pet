import unittest

from dragon_pet.dialogue import format_limits, pick_line


class DialogueTests(unittest.TestCase):
    def test_context_status_uses_k_and_does_not_invent_cache_rate(self):
        from dragon_pet.dialogue import format_context_usage
        self.assertIn('91.0k / 272.0k', format_context_usage((91000, 272000, 50)))
        self.assertIn('50%', format_context_usage((91000, 272000, 50)))
        self.assertIn('不可用', format_context_usage((91000, 272000, None)))
        self.assertIn('不可用', format_context_usage(None))
    def test_formats_remaining_not_used(self):
        result = {'rateLimits': {'primary': {'usedPercent': 98, 'windowDurationMins': 300},
                                 'secondary': {'usedPercent': 18, 'windowDurationMins': 10080}}}
        self.assertIn('五小时剩余 2%', format_limits(result))
        self.assertIn('每周剩余 82%', format_limits(result))

    def test_missing_limits_are_not_reported_as_zero(self):
        self.assertIn('不可用', format_limits({'rateLimits': {}}))

    def test_low_limit_is_called_out(self):
        result = {'rateLimits': {'primary': {'usedPercent': 95, 'windowDurationMins': 300}}}
        self.assertIn('不多', format_limits(result))

    def test_unknown_limit_does_not_claim_it_was_found(self):
        self.assertIn('暂时', format_limits({'rateLimits': {}}))

    def test_unexpected_duration_is_not_mislabeled(self):
        result = {'rateLimits': {'primary': {'usedPercent': 50, 'windowDurationMins': 60}}}
        self.assertIn('五小时额度不可用', format_limits(result))

    def test_dialogue_categories(self):
        for category in ('startup', 'interaction', 'sleep', 'wake'):
            self.assertTrue(pick_line(category))

    def test_consecutive_lines_do_not_repeat(self):
        previous = pick_line('interaction')
        for _ in range(50):
            current = pick_line('interaction')
            self.assertNotEqual(current, previous)
            previous = current


if __name__ == '__main__':
    unittest.main()
