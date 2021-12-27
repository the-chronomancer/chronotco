ChronoTCO
====

This is a rework of Reza Begheri's tail recursion approach, specifically his article_ Python Stack Frames and Tail-Call Optimization and his Tail Recursion code_. This was not forked due to the significance of the changes: providing Python 3.8x support, eliminating while loops, cleaning up all variable names and flow, stripping out non-decorator functionality, and creating it as an installable pip module that could then be easily digested. 

.. _article: https://towardsdatascience.com/python-stack-frames-and-tail-call-optimization-4d0ea55b0542. 
.. _code: https://github.com/reza-bagheri/tail-rec)

This is a proof of concept pip (**Python 3.x**) module that provides a decorator implementation of tail call optimization via bytecode manipulation, reducing the space complexity of recursion to **O(1)** (rather than **O(n)**) by manipulating the function structure itself.  

If a function is tail-call recursive and you want to ensure you won't blow the stack, use chronotco!

Installation
----

::

    $ pip install chronotco  


Usage
----
Import the decorator:

.. code:: python

    from chronotco import chronotco

And decorate your tail-recursive function!

.. code:: python

    @chronotco  
    def tail_factorial(n, accumulator=1):  
        if n == 0: 
            return accumulator  
        else: 
            return tail_factorial(n-1, accumulator * n)
            
Why?
----
Sorry Guido_, something more important than arguing whether or not TCO and losing stack traces is Pythonic, is that I learned something I did not know before!

.. _Guido: http://neopythonic.blogspot.com/2009/04/final-words-on-tail-calls.html

Support
----
This implementation is provided as-is with no support, it exists entirely for educational purposes.

License
-------
 - See `LICENSE <LICENSE>`__ for more information.
