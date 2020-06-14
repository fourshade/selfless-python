Selfless Python
===============

This library allows the creation of classes that do not use explicit 'self', instead functioning more like other OOP languages where methods can access fields and other methods of the current instance directly by name (so long as a function argument doesn't collide with it). There is only one module (selfless.py) and one class (Selfless) that comprise the entire public interface.

Requirements
------------

CPython 3.8 or higher.

Operation
---------

There are no installation scripts of any kind. Just drag the file "selfless.py" into a project folder and import it into other scripts in that folder using ``from selfless import Selfless``. By extending the base class Selfless, a bunch of Python voodoo will descend upon the new class and cleanse it of the need to declare self as the first parameter to methods:

::

    from selfless import Selfless

    class Foo(Selfless):

        var_a = None
        var_b = None
        multiplier = 2

        def __init__(a, b):
            var_a = a
            var_b = b

        def total():
            return var_a + var_b

        def mult_total():
            return multiplier * total()

The catch is that you *have* to declare all of your instance variables in the class body for them to be accessed this way. Setting them to None is fine; you can initialize them properly in __init__ anyway.

Explicit ``self`` is still technically allowed, but isn't really necessary unless you declare a method with arguments that have the same name as fields. If that's the case, you can do it the same way it is done in Java:

::

    class Bar(Selfless):

        a = None
        b = None

        def __init__(a, b):
            self.a = a
            self.b = b

Subclasses also work mostly the same, even allowing multiple inheritance with proper MRO resolution. You can't, however, have a class that inherits from both a selfless class and a normal class...the magic doesn't quite go that deep. A standard subclass might be declared like this:

::

    class FooExtended(Foo):

        var_c = None
        multiplier = 3

        def __init__(a, b, c):
            super.__init__(a, b)
            var_c = c

        def total():
            return super.total() + var_c

``super`` works only slightly differently in that you don't have to call() it, you just use it directly in the place where ``self`` would go. Since these two identifiers (``self`` and ``super``) have special treatment, you can change their names by overriding the attributes ``SELFNAME`` and ``SUPERNAME`` in subclasses. For a Java-style instance reference, you could do:

::

    class ReallySelfless(Selfless):

        SELFNAME = 'this'

        a = None

        def __init__(a):
            this.a = a

More Details
------------

In all seriousness, this is an **evil, evil hack** and should **not** be used for anything more substantial than toy examples or quick one-off scripts. The required mutation of functions and code objects is so invasive that your Python interpreter will probably need therapy afterward. Since it relies on bytecode hacking, it will only work in CPython, but I'm not sure how popular the other implementations really are. I know they tend to go to great lengths to ensure compatibility with CPython even down to implementation details, but there's just no way this would work with anything that doesn't use the exact same format of bytecode.

The code currently isn't optimized in any way, so its performance is going to be ghastly. Instance creation is horrifically expensive since the constructor basically hacks up a new set of bytecode objects and function closures for each one. Super method calls subvert these closures, so those end up being expensive as well. As for everything else...most field accesses and method calls are done by attribute lookup on 'self' in normal code, but these are replaced by cell dereferences in selfless classes. In *theory*, the cell dereference should be faster: it involves an array index and a pointer deref, while attribute access is normally a hash lookup. But attribute access is highly optimized in Python whereas cell dereference is rather uncommon and I wouldn't be surprised if there's a bit of extra overhead. In any case, profiling this code in detail could be impossible given the way it rearranges the internals of functions.

Most of the fundamental OOP object operations are covered by this code, but Python lets you do a lot of crazy things with objects that other languages don't. As a general guideline, if you try to do something with a selfless object that you couldn't do in Java, it may not do what you expect. It's honestly not worth covering all of the crazy corner cases that Python allows; at that point you might as well just use Java.
