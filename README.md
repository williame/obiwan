Obiwan.py
---------

[blogpost] http://williamedwardscoder.tumblr.com/post/33185451698/obiwan-typescript-for-python

Obiwan is a Python type-checker.  You place descriptive type constraints in your function declarations and obiwan can check them for you at runtime.

A function can look like:

    def example(a: int, b: float) -> number:
        return a/b

My ambition is that this Obiwan syntax is widely adopted and eventually Python static type checkers support it and IDEs can do auto-complete ala Typescript.

To enable obiwan, you just call it:

    from obiwan import *; install_obiwan_runtime_check()
    
you are now running obiwan!  Runtime execution will be slower, but annotated functions will be checked for parameter correctness!

All strings in your function annotations are ingored; you can place documentation in annotations without impacting obiwan.

You can also describe objects and dictionary parameters that are *duckable*:

    def example2(obj: {"a":int, "b": float}) -> {"ret": number}:
        return {"ret": a/b}
        
Duckable checking can support the checking of *optional* and *noneable* attributes:

    def example3(obj: {"a":int, optional("b"): float}):
        ...
        
Duckable checks can contain duckable attributes themselves too:

    def example4(person: {"name":str, "phone": {"type":str, "number":str}}):
        ...
        
You can specify alternative constraint types using sets:

    def example5(x: {int,float}):
        ...
        
In fact, *number* type is just a set of int and float.  And *noneable* is just a way of saying {...,None}

Lists mean that the attribute must be an array where each element matches the constraint e.g.:

    def example6(numbers: [int]):
        ...
        
You can provide your own complex custom constraint checkers by subclassing the ObiwanCheck class; look at obiwan.StringCheck for inspiration.

You can say that a parameter is callable using function:

    def example7(callback: function):
        ...
        
If you want, you can describe the parameters that the function should take:

    def example8(callback: function(int,str)):
        ...
        
However, all the functions passed to example8 must now be properly annotated with a matching annotation.

The special type any can be used if you do not want to check the type:

    def example9(callback: function(int,any,number)):
        ...
        
You can also specify that a function should support further arguments using ellipsis:

    def example10(callback: function(int,any,...)):
        ...
        
This will ensure that all callbacks have at least two parameters, the first being an int.

Utility functions to load and dump JSON are provided.  These support a new *template* parameter and validate the input/output matches the constraint e.g.:

    json.loads(tainted,template=[{"person":....}])
