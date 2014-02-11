import obiwan
import unittest


class TestNoneable(unittest.TestCase):

    def test_dict(self):
        template = {
            'person': [{
                'id': int,
                obiwan.noneable('name'): str
            }]
        }

        test = {'person': [{'id': 1, 'name': None}]}

        obiwan.duckable(test, template)
