Obiwan.py
---------

what is obiwan?
===============

[blogpost]
http://williamedwardscoder.tumblr.com/post/33185451698/obiwan-typescript-for-python

Obiwan is a Python type-checker. You place descriptive type constraints
in your function declarations and obiwan can check them for you at
runtime.

A function can look like:

::

    def example(a: int, b: float) -> number:
        return a/b

My ambition is that this Obiwan syntax is widely adopted and eventually
Python static type checkers support it and IDEs can do auto-complete ala
Typescript.

To enable obiwan, you just call it:

::

    from obiwan import *; install_obiwan_runtime_check()

you are now running obiwan! Runtime execution will be slower, but
annotated functions will be checked for parameter correctness!

All strings in your function annotations are ingored; you can place
documentation in annotations without impacting obiwan.

maturity
========

The dictionary and list checking code is based upon a tried-and-tested
JSON validator.

The integration with Python 3 function annotations is new and the
``function`` and ``duck`` type checking is new. Improvements and patches
welcome!

validating dictionaries and lists
=================================

You can also describe dictionary parameters and what their expected
attributes are:

::

    def example2(obj: {"a":int, "b": float}) -> {"ret": number}:
        return {"ret": a/b}
        

Checking can support the checking of *optional* and *noneable*
attributes:

::

    def example3(obj: {"a":int, optional("b"): float}):
        ...
        

Checks can contain dictionary and other attributes too:

::

    def example4(person: {"name":str, "phone": {"type":str, "number":str}}):
        ...
        

You can specify alternative constraint types using sets:

::

    def example5(x: {int,float}):
        ...
        

In fact, *number* type is just a set of int and float. And *noneable* is
just a way of saying ``{...,None}``

Lists mean that the attribute must be an array where each element
matches the constraint e.g.:

::

    def example6(numbers: [int]):
        ...
        

Tuples must map to lists or tuples (no destructive iterators!) with the
appropriate types in each slot:

::

    def nearest_point_on_line(line:((int,int),(int,int)),pt:(int,int)) -> (int,int):

Within tuples you can use ``any`` to indicate that a type needs not be
checked, and you can use ellipsis as the last element in the
type-defintion tuple to indicate that additional parameters are allowed:

::

    def decode_data(data: str) -> (str,any,int,...):
        

It aids readability to use variables to hold definitions e.g.:

::

    Point = (int,int)
    def nearest_point_on_line(line:(Point,Point),pt:Point) -> Point:

and:

::

    api_add_user = {
        "name": str,
        "admin": bool,
    }
    def add_user(user: api_add_user) -> int:
        ...
        

Dict templates can have a special *options* key which is a list of
options. Options include *strict* and *subtype*:

::

    api_base = {
        "user_id": int,
    }
    api_set_name = {
        options: [strict, subtype(api_base)],
        "name": str,
    }

*Strict* will complain if the dictionary being validated contains any
keys *not* in the template dictionary, and *subtype* will combine
parameters specified in other dictionary templates with this template.
In this example, dictionaries validated against ``api_set_name`` must
have both user\_id and name specified, and no other keys.

You can specify multiple parent templates in the subtype arguments, and
have multiple subtype options, and nest template inheritence arbitrarily
deep.

validating JSON
===============

Utility functions to load and dump JSON are provided. These support a
new *template* parameter and validate the input/output matches the
constraint e.g.:

::

    json.loads(tainted,template=[api_add_user])

if it quacks like a duck...
===========================

In Python 3 everything is an object, even ``int`` and ``None``. So you
can't generically say that an argument or attribute must be an *object*.
You have to say what its attributes should be. This follows the same
style as validating dictionaries, but uses the *duck* type and keyword
arguments to define:

::

    def example7(a: duck(name=str,get_name=function)):
        ...
        

This means that ``a`` must be something with a name attribute of type
string, and a function attribute called get\_name.

You can of course use classes to:

::

    class Person:
       def get_name(self):
          ...

    def example8(person: Person):
        ...
        

*duck* instances can *extend* other duck instances using positional
parameters:

::

    api_base = duck(user_id=int)
    api_change_name = duck(api_base, name=str)
    def change_name(user: api_change_name):
        ...
        

validating callbacks
====================

You can say that a parameter is callable using function:

::

    def example9(callback: function):
        ...
        

If you want, you can describe the parameters that the function should
take:

::

    def example10(callback: function(int,str)):
        ...
        

However, all the functions passed to example8 must now be properly
annotated with a matching annotation.

The special type any can be used if you do not want to check the type:

::

    def example11(callback: function(int,any,number)):
        ...
        

You can also specify that a function should support further arguments
using ellipsis:

::

    def example12(callback: function(int,any,...)):
        ...
        

This will ensure that all callbacks have at least two parameters, the
first being an int.

using lambdas as checkers
=========================

You can use lambdas as checkers; they should return a boolean condition
e.g.

::

    template = {
        'month': lambda x: x in ["jan","feb","mar",...],
        ...
    }

writing your own custom checkers
================================

You can provide your own complex custom constraint checkers by
subclassing the ObiwanCheck class; look at obiwan.StringCheck for
inspiration.
