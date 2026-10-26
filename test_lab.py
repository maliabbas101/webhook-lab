import unittest

from lab import simulate


class SimulationTests(unittest.TestCase):
    def test_retries_use_exponential_backoff(self):
        result = simulate({'statuses': [500, 429, 200], 'copies': 1})
        self.assertEqual([row['at'] for row in result['rows']], [0, 1, 3])
        self.assertEqual(result['processed'], 1)

    def test_duplicate_is_acknowledged_without_processing(self):
        result = simulate({'statuses': [200], 'copies': 2})
        self.assertEqual(result['processed'], 1)
        self.assertEqual(result['rows'][-1]['outcome'], 'duplicate skipped')

    def test_disabling_deduplication_repeats_processing(self):
        self.assertEqual(simulate({'statuses': [200], 'deduplicate': False})['processed'], 2)

    def test_permanent_error_is_not_retried(self):
        result = simulate({'statuses': [400, 200], 'copies': 1})
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['failed_deliveries'], 1)

    def test_retry_budget_is_bounded(self):
        result = simulate({'statuses': [503], 'attempts': 3, 'copies': 1})
        self.assertEqual(len(result['rows']), 3)
        self.assertEqual(result['rows'][-1]['wait'], 0)
        self.assertEqual(result['failed_deliveries'], 1)

    def test_invalid_inputs(self):
        for config in ({'copies': True}, {'attempts': 0}, {'statuses': []}, {'statuses': ['500']}, {'deduplicate': 'false'}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                simulate(config)


if __name__ == '__main__':
    unittest.main()
