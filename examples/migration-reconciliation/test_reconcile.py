import tempfile
import unittest
from pathlib import Path
from reconcile import read_snapshot, reconcile


class ReconciliationTests(unittest.TestCase):
    def test_missing_zero_and_deltas_remain_distinct(self):
        _, rows = reconcile([('zero', 0), ('lost', 2), ('changed', 10)],
                            [('zero', 0), ('new', 3), ('changed', 8)])
        self.assertEqual(rows, [('changed', 10, 8, -2, 'review'),
                                ('lost', 2, None, None, 'missing_target'),
                                ('new', None, 3, None, 'missing_source'),
                                ('zero', 0, 0, 0, 'match')])

    def test_bad_inputs_are_rejected(self):
        cases = ['resource,count\nx,1\nx,2\n', 'resource,count\nx,-1\n',
                 'resource,count\nx,1.5\n', 'resource,count\n,2\n',
                 'resource,count\n', 'wrong,count\nx,1\n']
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.csv'
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        read_snapshot(path)


if __name__ == '__main__':
    unittest.main()
