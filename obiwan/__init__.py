import weakref
import inspect
import gc
import types
import opcode
import decimal
import atexit
import sys
import collections

_enabled = False


class ObiwanError(Exception):
    "Thrown by Obiwan checker if a function call or object definition does not match at runtime"


class ObiwanCheck:
    "subclass this for custom checks"
    def check(self, obj, ctx):
        "perform your custom check here; if fails, please throw a ObiwanError"
        raise NotImplementedError("subclasses of ObiwanCheck must override check()")


class duck(ObiwanCheck):
    "something that has specified attributes"
    def __init__(self, *extends, **attributes):
        duckable(extends, [lambda obj: isinstance(obj, duck)], "duckable template extends")
        self.extends = extends
        self.attributes = attributes

    def check(self, obj, ctx, checked=None):
        if checked is None and self.extends:
            checked = set()
        for name, value in self.attributes.items():
            if checked is not None:
                if name in checked:
                    continue
                checked.add(name)
            if isinstance(value, optional):
                if not hasattr(obj, name):
                    continue
                value = value.template
            if not hasattr(obj, name):
                raise ObiwanError("%s does not have a %s" % (ctx, name))
            duckable(getattr(obj, name), value, "%s.%s" % (ctx, name))
        for parent in self.extends:
            parent.check(obj, ctx, checked)


class function(ObiwanCheck):
    """something that is callable; there are two ways to use this class:
        1) arg: function, ...
        in this case arg must be callable; the signature is not checked
        2) arg: function(int,float,...)
        the signature is checked; all functions passed must have this type signature
    """
    @classmethod
    def is_function(cls, obj):
        return hasattr(obj, "__call__")

    @classmethod
    def check_is_function(cls, obj, ctx):
        if not cls.is_function(obj):
            raise ObiwanError("%s is %s, not a function" % (ctx, type(obj)))

    def __init__(self, *args):
        self.ellipsis = args.count(Ellipsis)
        if self.ellipsis:
            if self.ellipsis != 1:
                raise ObiwanError("bad template: %s ellipsis can only occur at end of function types" % args)
            if args[-1] != Ellipsis:
                raise ObiwanError("bad template: %s ellipsis can only occur at end of function types" % args)
            self.args = args[:-1]
        else:
            self.args = args

    def check(self, obj, ctx):
        self.check_is_function(obj, ctx)
        try:
            args = inspect.getfullargspec(obj)
        except TypeError:
            raise ObiwanError("%s is not a Python function" % ctx)
        if not args.annotations:
            raise ObiwanError("%s is not annotated" % ctx)
        if len(args.args) < len(self.args):
            raise ObiwanError("%s has too few arguments" % ctx)
        if not self.ellipsis and (len(args.args) > len(self.args)):
            raise ObiwanError("%s has too many arguments" % ctx)
        for arg, name in zip(self.args, args.args):
            if (arg is any) or isinstance(arg, str):
                continue
            got = args.annotations.get(name, None)
            if got is None:
                raise ObiwanError("%s %s(%s) is not annotated" % (ctx, obj.__name__, name))
            if (got is any) or isinstance(got, str):
                continue
            sametype(arg, got, "%s(%s)" % (ctx, name))


class StringCheck(ObiwanCheck):
    "an example check that ensures strings are within certain size limits"
    def __init__(self, maxlen, minlen=0):
        self.minlen, self.maxlen = minlen, maxlen

    def check(self, s, ctx):
        if not isinstance(s, str):
            raise ObiwanError("%s must be a string" % ctx)
        if len(s) < self.minlen:
            raise ObiwanError("%s is %d long, but must be more than %d" % (ctx, len(s), self.minlen))
        if len(s) > self.maxlen:
            raise ObiwanError("%s is %d long, but must be less than %d" % (ctx, len(s), self.maxlen))


class DecimalCheck(ObiwanCheck):
    "an example check that ensures values are string representations of decimal numbers"
    def check(self, s, ctx):
        try:
            decimal.Decimal(s)
        except:
            raise ObiwanError("%s is %s but should be a string containing a decimal value" % (ctx, type(s)))


class optional:
    def __init__(self, key):
        self.key = key
    def __eq__(self, other):
        return isinstance(other, optional) and other.key == self.key
    def __hash__(self):
        return hash(self.key)


class noneable:
    def __init__(self, template):
        self.template = template


number = {int, float}  # a type that is a number


options = object() # marker for dict templates e.g. { options: [strict]
strict = object() # attribute for dict template options

class subtype:
    def __init__(self, *types):
        duckable(types, [dict], "subtype constructor")
        self.types = types
    def template(self):
        template = {}
        for parent in self.types:
            for key, value in parent.items():
                if key is options:
                    for opt in value:
                        if isinstance(opt, subtype):
                            template.update(opt.template())
                else:
                    template[key] = value
        return template


def sametype(expect, got, ctx):
    "raises an ObiwanError if the type declarations are incompatible"
    if expect == got:
        return
    if isinstance(got, set) and expect in got:
        return
    raise ObiwanError("%s expects %s but got %s" % (ctx, expect, got))
    
    
def _check_function_template(obj, template, ctx=""):
    raise ObiwanError("checking function templates is not supported yet")
    obj_ret = None
    if inspect.isclass(obj): # classes are callable too
        obj_ret = obj
        obj = obj.__init__
    if not inspect.isfunction(obj):
        raise ObiwanException("%s %s is not a function" % (ctx, obj))
    try:
        expect = inspect.signature(template)
    except TypeError:
        raise ObiwanException("%s template %s is not a function" % (ctx, template))
    except ValueError:
        raise ObiwanException("%s cannot extract signature from template %s" % (ctx, template))
    try:
        got = inspect.signature(obj)
    except (TypeError, ValueError):
        raise ObiwanException("%s cannot extract signature from %s" % (ctx, obj))
    expect_return = expect.return_annotation if expect.return_annotation is not inspect.Signature.empty else None
    got_return = obj_ret or (got.return_annotation if got.return_annotation is not inspect.Signature.empty else None)
    if bool(expect_return) != bool(got_return) and expect_return is not any:
        raise ObiwanException("%s function %s does not return %s" % (ctx, got, expect_return))
    ##### We need to check signatures not values
    if expect_return and expect_return is not any:
        duckable(got_return, expect_return, "%s return" % ctx)
    expect_params = expect.parameters.values()
    got_params = got.parameters.values()
    if len(expect_params) != len(got_params):
        raise ObiwanException("%s function %s mismatches %s" % (ctx, got, expect))
    for i, (g, e) in enumerate(zip(got_params, expect_params)):
        if e.annotation is inspect.Parameter.empty or e.annotation is any:
            continue
        if g.annotation is inspect.Parameter.empty:
            raise ObiwanException("%s function %s parameter %s should be %s but is unannotated" % (ctx, got, i, e.annotation))
        duckable(g.annotation, e.annotation, "%s function %s parameter %d" % (ctx, got, i))
    

def duckable(obj, template, ctx="checking"):
    try:
        if isinstance(template, str):  # allow docstrings
            return
        if isinstance(template, optional):
            if obj is None:
                return
            template = template.template
        elif isinstance(template, noneable):
            if obj is not None:
                duckable(obj, template.template, ctx)
        elif template is any:
            pass
        elif template is function:
            function.check_is_function(obj, ctx)
        elif isinstance(template, ObiwanCheck):
            template.check(obj, ctx)
        elif isinstance(template, set):
            if len(template) == 1: # we expect a set, all of a particular type
                typ = tuple(template)[0]
                if not isinstance(obj, set):
                    raise ObiwanError("%s is %s but should be a set of %s" % (ctx, type(obj), typ))
                for i, o in enumerate(obj):
                    duckable(o, typ, ctx + ("[%d" % i))
            else: # leaf datatype multiple-choice
                for typ in template:
                    try:
                        duckable(obj, typ, ctx)
                        break
                    except ObiwanError:
                        pass
                else:
                    raise ObiwanError("%s is %s but should be one of %s" % (ctx, type(obj), template))
        elif isinstance(template, dict):
            if not isinstance(obj, dict):
                raise ObiwanError("%s is %s but should be a dict" % (ctx, type(obj)))
            if options in template:
                is_strict = False
                for opt in template[options]:
                    if opt is strict:
                        if is_strict:
                            raise ObiwanError("%s template specifies strict option twice" % ctx)
                        is_strict = True
                    elif isinstance(opt, subtype):
                        tmpl = opt.template()
                        tmpl.update(template)
                        template = tmpl
                    else:
                        raise ObiwanError("%s unsupported template option %s: %s" % (ctx, type(opt), opt))
                if is_strict:
                    for key in obj:
                        if not key in template and not optional(key) in template:
                            raise ObiwanError("%s should not have a child called %s" % (ctx, key))
            for key, value in template.items():
                if key is options:
                    continue
                elif isinstance(key, optional):
                    key = key.key
                    if key not in obj:
                        continue
                elif isinstance(key, noneable):
                    key = key.template
                    if obj[key] is None:
                        continue
                elif isinstance(key, str):
                    if key not in obj:
                        raise ObiwanError("%s should have child called %s" % (ctx, key))
                    duckable(obj[key], value, "%s[\"%s\"]" % (ctx, key))
                else: # ensure that *all* keys and values are of right type in dict
                    for k, v in obj.items():
                        duckable(k, key, "key %s[%s]" % (ctx, k))
                        duckable(v, value, "key %s[\"%s\"]" % (ctx, k))
        elif isinstance(template, list):
            if not isinstance(obj, collections.abc.Sequence):
                raise ObiwanError("%s is %s but should be %s" % (ctx, type(obj), template))
            if len(template) != 1:
                raise ObiwanError("%s bad template: %s lists must all be of the same type" % (ctx, template))
            template = template[0]
            for i, item in enumerate(obj):
                duckable(item, template, "%s[%s]" % (ctx, i))
        elif isinstance(template, tuple):
            if not isinstance(obj, collections.abc.Sequence):
                raise ObiwanError("%s is %s but should be packed %s" % (ctx, type(obj), template))
            for i, expect in enumerate(template):
                if expect is any:
                    continue
                if expect is Ellipsis:
                    return
                if i >= len(obj):
                    raise ObiwanError("%s[%d] %s but should be packed %s but is omitted" % (ctx, i, expect))
                got = obj[i]
                duckable(got, expect, "%s[%d]" % (ctx, i))
            if len(template) != len(obj):
                raise ObiwanError("%s is %s but should be packed %s" % (ctx, type(obj), template))
        elif template is duck:
            raise ObiwanError("%s you must instansiate a duck and describe its expected attributes" % ctx)
        elif hasattr(template, "__name__") and template.__name__ == "<lambda>":
            if not template(obj):
                raise ObiwanError("%s failed lambda check" % ctx)
        elif inspect.isfunction(template): # lambdas are also functions, so check for lambda first
            _check_function_template(obj, template)
        else:  # single type
            try:
                if not isinstance(obj, template):
                    raise ObiwanError("%s is %s but should be %s" % (ctx, obj, template))
            except TypeError:
                raise ObiwanError("%s template %s is not a valid type template" % (ctx, template))
    except ObiwanError:
        raise
    except Exception as e:
        raise ObiwanError("%s internal error: %s" % (ctx, e))

def is_duckable(*args):
    try:
        duckable(*args)
        return True
    except ObiwanError:
        return False
        
        
def check(*args):
    global _enabled
    if _enabled:
        duckable(*args)

import json as _json


class json:
    "a wrapper around Python's JSON that enables validation"
    @classmethod
    def _dump(cls, func, obj, *args, **kwargs):
        template = kwargs.pop("template", None)
        if template is not None:
            duckable(obj, template, "json validation ")
        return func(obj, *args, **kwargs)

    @classmethod
    def dump(cls, *args, **kwargs):
        return cls._dump(_json.dump, *args, **kwargs)

    @classmethod
    def dumps(cls, *args, **kwargs):
        return cls._dump(_json.dumps, *args, **kwargs)

    @classmethod
    def _load(cls, func, *args, **kwargs):
        template = kwargs.pop("template", None)
        ret = func(*args, **kwargs)
        if template is not None:
            duckable(ret, template, "json validation ")
        return ret

    @classmethod
    def load(cls, *args, **kwargs):
        return cls._load(_json.load, *args, **kwargs)

    @classmethod
    def loads(cls, *args, **kwargs):
        return cls._load(_json.loads, *args, **kwargs)


_annotation_cache = weakref.WeakKeyDictionary()


def _runtime_checker(frame, evt, arg):
    global _enabled
    if not _enabled:
        return
    if evt == "call":
        # we cache those we've looked up
        # we use frame.f_code itself as key;
        if not frame.f_code in _annotation_cache:
            # we assume that first gc referrer is the function itself
            # this code seems very fragile and hackish;
            # TODO much nicer to use inspect.signature(frame) if that works in Python 3.3...
            frame_info = [obj for obj in gc.get_referrers(frame.f_code) if isinstance(obj, types.FunctionType)]
            # does the first gc referrer have annotations?
            if frame_info and hasattr(frame_info[0], "__annotations__") and frame_info[0].__annotations__:
                frame_info = frame_info[0]
            else:
                frame_info = None
            _annotation_cache[frame.f_code] = frame_info
        else:
            frame_info = _annotation_cache[frame.f_code]
        # frame_info is set to a function object with annoations?
        if frame_info:
            return_intercept = None
            for key, constraint in frame_info.__annotations__.items():
                if key == "return":  # we want to track the return type too
                    return_intercept = _runtime_checker
                    continue
                arg = frame.f_locals[key]
                duckable(arg, constraint, "%s(%s)" % (frame.f_code.co_name, key))
            return return_intercept
    elif evt == "return":
        if (arg is not None) or (opcode.opname[frame.f_code.co_code[frame.f_lasti]] in ('RETURN_VALUE', 'YIELD_VALUE')):
            frame_info = _annotation_cache[frame.f_code]
            constraint = frame_info.__annotations__["return"]
            duckable(arg, constraint, "%s()->" % frame.f_code.co_name)
        # else we are in an exception! Super messy horrid hack code
        # http://stackoverflow.com/a/12800909/15721

def install_obiwan_runtime_check():
    global _enabled
    _enabled = True
    sys.settrace(_runtime_checker)
    def disable():
        global _enabled
        _enabled = False
    atexit.register(disable)
