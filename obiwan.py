
class ObiwanError(Exception):
    "Thrown by Obiwan checker if a function call or object definition does not match at runtime"

class ObiwanCheck(object):
    "subclass this for custom checks"
    def check(self,obj,ctx):
        "perform your custom check here; if fails, please throw a ObiwanError"
        raise NotImplementedError("subclasses of ObiwanCheck must override check()")
        
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

class optional(object):
    def __init__(self,template):
        self.template = template
        
class noneable(object):
    def __init__(self,template):
        self.template = template

number = (int,float) # a type that is a number

def duckable(obj,template,ctx=""):        
    def check(path,obj,tmpl):
        if isinstance(tmpl,noneable):
            if obj is not None:
                check(path,obj,tmpl.template)
        elif isinstance(tmpl,ObiwanCheck):
            tmpl.check(obj)
        elif isinstance(tmpl,tuple): # leaf datatype multiple-choice
            for typ in tmpl:
                try:
                    check(path,obj,typ)
                    break
                except ObiwanError:
                    pass
            else:
                raise ObiwanError("%s is %s but should be one of %s"%(path,type(obj),tmpl))
        elif isinstance(tmpl,dict):
            if not isinstance(obj,dict):
                raise ObiwanError("%s is %s but should be an object"%(path,type(obj)))
            # test explicit values
            for key,value in tmpl.items():
                if isinstance(key,optional):
                    key = key.template
                    if key not in obj:
                        continue
                elif key not in obj:
                    raise ObiwanError("%s should have child called %s"%(path,key))
                check("%s[\"%s\"]"%(path,key),obj[key],value)
        elif isinstance(tmpl,list):
            if not isinstance(obj,(tuple,list)):
                raise ObiwanError("%s is %s but should be a list"%(path,type(obj)))
            assert len(tmpl)==1
            for i,item in enumerate(obj):
                check("%s[%s]"%(path,i),item,tmpl[0])
        else: # single type
            if not isinstance(obj,tmpl):
                raise ObiwanError("%s is %s but should be %s"%(path,type(obj),tmpl))
    check(ctx,obj,template)
    

import json as _json

class json(object):
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
                if isinstance(constraint,str): # allow docstrings
                    continue
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

