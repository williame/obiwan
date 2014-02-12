import obiwan
import unittest


class TestNoneable(unittest.TestCase):

    def test_dict(self):
        template = {
            'person': [{
                'id': int,
                obiwan.noneable('name'): str,
                obiwan.optional('age'): int
            }]
        }

        tests = [
            {'person': [{'id': 1, 'name': None}]},
            {'person': [{'id': 1, 'name': None, 'age': 14}]},
            {'person': [{'id': 1, 'name': "Adam"}]}
        ]

        for test in tests:
            obiwan.duckable(test, template)
