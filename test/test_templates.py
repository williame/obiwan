import obiwan
import unittest


class Tests(unittest.TestCase):

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
            
            
    def test_lambda(self):
        template = {
            'id':   lambda obj: isinstance(obj, int),
        }
        
        obiwan.duckable({'id': 1}, template)
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable, {'id': 'a'}, template)
        
        
    def test_strict(self):
        template = {
            obiwan.options: [obiwan.strict],
            'id': int,
            obiwan.optional('opt'): int,
        }
        
        obiwan.duckable({'id': 1}, template)
        obiwan.duckable({'id': 1, 'opt': 2}, template)
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable, {'id': 1, 'x': 2}, template)
        
        
    def test_subtype(self):
        base = {
            'id': int,
        }
        parent = {
            obiwan.options: [obiwan.subtype(base)],
            obiwan.optional('y'): int,
        }
        template = {
            obiwan.options: [obiwan.strict, obiwan.subtype(parent)],
            'x': int,
        }

        obiwan.duckable({'id': 1, 'x': 2}, template)
        obiwan.duckable({'id': 1, 'x': 2, 'y': 3}, template)
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable, {'id': 1}, template)        
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable, {'id': 1, 'x': 2, 'z': 3}, template)


    def test_duck_extends(self):
        base = obiwan.duck(id=int)
        parent = obiwan.duck(base)
        template = obiwan.duck(parent,x=int)
        
        class Obj:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        template.check(Obj(id=1, x=2), 1)
        self.assertRaises(obiwan.ObiwanError, template.check, Obj(id=1), 2)


    def test_bad(self):
        template = {
            'person': [{
                    'id': int,
                    'name': str,
                    'age': int,
            }],
        }
        
        tests = [
            {'person': None },
            {'person': 1 },
            {'person': {'id': 1 }},
            {'person': [{'id': 'str'}]},
            {'person': [{'id': 1, 'name': 'abc', 'age': 14}, 2]},
        ]
        
        for test in tests:
            with self.assertRaises(obiwan.ObiwanError, msg=test):
                obiwan.duckable(test, template)


    def test_dict_of_types(self):
        obiwan.duckable({"a": 1, "b": 2}, {str: int})
        obiwan.duckable({"a": 1, "b": 2}, {"a": int, str: int})
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable,
            {"a": 1, "b": None}, {str: int})
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable,
            {"a": 1, 2: 2}, {str: int})
        
       
    def test_set_of_type(self):
        obiwan.duckable(set(), {str})
        obiwan.duckable({"a", "b"}, {str})
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable,
            {1, 2}, {str})
        self.assertRaises(obiwan.ObiwanError, obiwan.duckable,
            {"a", "b", ("a",)}, {str})
        
        
    def test_disabling(self):
        self.assertTrue(obiwan._enabled)
        obiwan._enabled = False
        obiwan.check({}, {"k":str}) # would fail if obiwan were enabled
        obiwan._enabled = True
        self.assertRaises(obiwan.ObiwanError, obiwan.check,
            {}, {"k":str})        
