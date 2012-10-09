import inspect

class ObiwanError(Exception):
    "Thrown by Obiwan checker if a function call or object definition does not match at runtime"

class ObiwanCheck:
    "subclass this for custom checks"
    def check(self,obj,ctx):
        "perform your custom check here; if fails, please throw a ObiwanError"
        raise NotImplementedError("subclasses of ObiwanCheck must override check()")
        
class function(ObiwanCheck):
    """something that is callable; there are two ways to use this class:
        1) arg: function, ...
        in this case arg must be callable; the signature is not checked
        2) arg: function(int,float,...)
        the signature is checked; all functions passed must have this type signature
    """
    def __init__(self,*args):
        self.ellipsis = args.count(Ellipsis)
        if self.ellipsis:
            assert self.ellipsis == 1, "Ellipsis can only occur at end of function types"
            assert args[-1] == Ellipsis, "Ellipsis can only occur at end of function types"
            self.args = args[:-1]
        else:
            self.args = args
    def check(self,obj,ctx):
        if not hasattr(obj,"__call__"):
            raise ObiwanError("%s is not callable"%ctx)
        args = inspect.getfullargspec(obj)
        if not args.annotations:
            raise ObiwanError("%s is not annotated"%ctx)
        if len(args.args) < len(self.args):
            raise ObiwanError("%s has too few arguments"%ctx)
        if not self.ellipsis and (len(args.args) > len(self.args)):
            raise ObiwanError("%s has too many arguments"%ctx)
        for arg,name in zip(self.args,args.args):
            if (arg is any) or isinstance(arg,str):
                continue
            got = args.annotations.get(name,None)
            if got is None:
                raise ObiwanError("%s %s(%s) is not annotated"%(ctx,obj.__name__,name))
            if (got is any) or isinstance(got,str):
                continue
            sametype(arg,got,"%s(%s)"%(ctx,name))

class StringCheck(ObiwanCheck):
    "an example check that ensures strings are within certain size limits"
    def __init__(self,maxlen,minlen=0):
        self.minlen, self.maxlen = minlen, maxlen
    def check(self,s,ctx):
        if not isinstance(s,str):
            raise ObiwanError("%s must be a string"%ctx)
        if len(s) < minlen:
            raise ObiwanError("%s is %d long, but must be more than %d"%(ctx,len(s),minlen))
        if len(s) > maxlen:
            raise ObiwanError("%s is %d long, but must be less than %d"%(ctx,len(s),maxlen))

class DecimalCheck(ObiwanCheck):
    "an example check that ensures values are string representations of decimal numbers"
    def check(self,s,ctx):
        try:
            Decimal(obj)
        except:
            raise ObiwanError("%s is %s but should be a string containing a decimal value"%(ctx,type(obj)))

class optional:
    def __init__(self,key):
        self.key = key
        
class noneable:
    def __init__(self,template):
        self.template = template

number = {int,float} # a type that is a number

def sametype(expect,got,ctx):
    "raises an ObiwanError if the type declarations a and b are incompatible"
    if expect==got:
        return
    if isinstance(got,set) and expect in got:
        return
    raise ObiwanError("%s expects %s but got %s"%(ctx,expect,got))

def duckable(obj,template,ctx=""):        
    if isinstance(template,str): # allow docstrings
        pass
    elif isinstance(template,noneable):
        if obj is not None:
            duckable(obj,template.template,ctx)
    elif template is function:
        if not hasattr(obj,"__call__"):
            raise ObiwanError("%s is not callable"%ctx)
    elif isinstance(template,ObiwanCheck):
        template.check(obj,ctx)
    elif isinstance(template,set): # leaf datatype multiple-choice
        for typ in template:
            try:
                duckable(obj,typ,ctx)
                break
            except ObiwanError:
                pass
        else:
            raise ObiwanError("%s is %s but should be one of %s"%(ctx,type(obj),template))
    elif isinstance(template,dict):
        if not isinstance(obj,dict):
            raise ObiwanError("%s is %s but should be an object"%(ctx,type(obj)))
        for key,value in template.items():
            if isinstance(key,optional):
                key = key.key
                if key not in obj:
                    continue
            elif key not in obj:
                raise ObiwanError("%s should have child called %s"%(ctx,key))
            duckable(obj[key],value,"%s[\"%s\"]"%(ctx,key))
    elif isinstance(template,list):
        if not isinstance(obj,(tuple,list)):
            raise ObiwanError("%s is %s but should be a list"%(ctx,type(obj)))
        assert len(template)==1, "lists must all be of the same type"
        template = template[0]
        for i,item in enumerate(obj):
            duckable(item,template,"%s[%s]"%(ctx,i))
    elif isinstance(template,tuple):
        if not isinstance(obj,(tuple,list)):
            raise ObiwanError("%s is %s but should be packed %s"%(ctx,type(obj),template))
        for i,expect in enumerate(template):
            if expect is any:
                continue
            if expect is Ellipsis:
                return
            if i >= len(obj):
                raise ObiwanError("%s[%d] %s but should be packed %s but is omitted"%(ctx,i,expect))
            got = obj[i]
            duckable(got,expect,"%s[%d]"%(ctx,i))
        if len(template) != len(obj):
            raise ObiwanError("%s is %s but should be packed %s"%(ctx,type(obj),template))
    else: # single type
        if not isinstance(obj,template):
            raise ObiwanError("%s is %s but should be %s"%(ctx,type(obj),template))
    
def is_duckable(obj,template,ctx=""):
    try:
        duckable(obj,template,ctx)
        return True
    except ObiwanError:
        return False

import json as _json

class json:
    "a wrapper around Python's JSON that enables validation"
    @classmethod
    def _dump(cls,func,obj,*args,**kwargs):
        template = kwargs.pop("template",None)
        if template is not None:
            duckable(obj,template,"json validation ")
        return func(obj,*args,**kwargs)
    @classmethod
    def dump(cls,*args,**kwargs):
        return cls._dump(_json.dump,*args,**kwargs)
    @classmethod
    def dumps(cls,*args,**kwargs):
        return cls._dump(_json.dumps,*args,**kwargs)
    
    @classmethod
    def _load(cls,func,*args,**kwargs):
        template = kwargs.pop("template",None)
        ret = func(*args,**kwargs)
        if template is not None:
            duckable(ret,template,"json validation ")
        return ret
    @classmethod
    def load(cls,*args,**kwargs):
        return cls._load(_json.load,*args,**kwargs)
    @classmethod
    def loads(cls,*args,**kwargs):
        return cls._load(_json.loads,*args,**kwargs)

import gc, types

def _runtime_checker(frame,evt,arg):
    if evt=="call":
        # we cache those we've looked up
        # we use frame.f_code itself as key;
        # TODO review if we need WeakReferences
        if not frame.f_code in _runtime_checker.lookup:
            # we assume that first gc referrer is the function itself
            # this code seems very fragile and hackish;
            # TODO much nicer to use inspect.signature(frame) if that works in Python 3.3...
            frame_info = [obj for obj in gc.get_referrers(frame.f_code) if isinstance(obj, types.FunctionType)]
            # does the first gc referrer have annotations?
            if frame_info and hasattr(frame_info[0],"__annotations__") and frame_info[0].__annotations__:
                frame_info = frame_info[0]
            else:
                frame_info = None
            _runtime_checker.lookup[frame.f_code] = frame_info
        else:
            frame_info = _runtime_checker.lookup[frame.f_code]
        # frame_info is set to a function object with annoations?
        if frame_info:
            return_intercept = None
            for key,constraint in frame_info.__annotations__.items():
                if key=="return": # we want to track the return type too
                    return_intercept = _runtime_checker
                    continue
                arg = frame.f_locals[key]
                duckable(arg,constraint,"%s(%s) "%(frame.f_code.co_name,key))
            return return_intercept
    elif evt=="return":
        frame_info = _runtime_checker.lookup[frame.f_code]
        constraint = frame_info.__annotations__["return"]
        duckable(arg,constraint,"%s()-> "%frame.f_code.co_name)

def install_obiwan_runtime_check():
    if hasattr(_runtime_checker,"enabled") and _runtime_checker.enabled:
        return
    import sys
    sys.settrace(_runtime_checker)
    _runtime_checker.lookup = {}
    _runtime_checker.enabled = True

