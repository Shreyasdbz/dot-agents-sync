import unittest

from cache import cached_amount


class CacheTests(unittest.TestCase):
    def test_existing_zero_amount_does_not_charge(self):
        calls = []
        cache = {"order": 0}
        self.assertEqual(cached_amount(cache, "order", calls.append), 0)
        self.assertEqual(calls, [])
        self.assertEqual(cache, {"order": 0})

    def test_existing_positive_amount(self):
        calls = []
        self.assertEqual(cached_amount({"order": 12}, "order", calls.append), 12)
        self.assertEqual(calls, [])

    def test_miss_stores_result(self):
        cache = {}
        self.assertEqual(cached_amount(cache, "order", lambda _: 12), 12)
        self.assertEqual(cache, {"order": 12})


if __name__ == "__main__":
    unittest.main()
