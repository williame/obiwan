Obiwan.py
---------

Obiwan is a Python type-checker.  You place descriptive type constraints in your function declarations and obiwan can check them for you at runtime.

A function can look like:

    def example(a: int, b: float) -> number:
        return a/b
    
To enable obiwan, you just call it:

    from obiwan import *; install_obiwan_runtime_check()
    
you are now running obiwan!  Runtime execution will be slower, but annotated functions will be checked for parameter correctness!

You can also describe objects and dictionary parameters that are *duckable*:

    def example2(obj: {"a":int, "b": float}) -> {"ret": number}:
        return {"ret": a/b}
        
Duckable checking can support the checking of *optional* and *noneable* attributes:

    def example3(obj: {"a":int, optional("b"): float}):
        ...
        
Duckable checks can contain duckable attributes themselves too:

    def example4(person: {"name":str, "phone": {"type":str, "number":str}}):
        ...
        
You can specify alternative constraint types using tuples:

    def example5(x: (int,float)):
        ...
        
In fact, *number* type is just a tuple of int and float.  And *noneable* is just an alternative way of saying (...,None)

Lists mean that the attribute must be an array where each element matches the constraint e.g.:

    def example6(numbers: [int]):
        ...
        
You can provide your own complex custom constraint checkers by subclassing the ObiwanCheck class; look at obiwan.StringCheck for inspiration.

Utility functions to load and dump JSON are provided.  These support a new *template* parameter and validate the input/output matches the constraint e.g.:

    json.loads(tainted,template=[{"person":....}])
