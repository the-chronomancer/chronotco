ChronoTCO
====

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
Recursion in Python creates a new stack frame every time it iterates through the loop. Though you can modify the recursion depth for your system, you will eventually exhaust all memory while retaining all previous iterations. This method of tail-call optimization determines if a function is tail-recursive, and if true, resets the function variables then jumps back to the beginning of the function, recycling the same stack frame.

An example of calling the above tail_factorial method without tail-call optimization and an input of 25,000 (default recursion depth is 1,000) yields a "**RecursionError: maximum recursion depth exceeded in comparison**", with chronotco you will see a 99,094 digit number assuming you have enough memory to store the full stack frame.

Sorry Guido_, something more important than arguing whether or not TCO and losing stack traces is Pythonic, is that I learned something I did not know before and used your language as a medium to do so!

.. _Guido: http://neopythonic.blogspot.com/2009/04/final-words-on-tail-calls.html

Support
----
This implementation is provided as-is with no support, it exists entirely for educational purposes.

License
-------
 - See `LICENSE <LICENSE>`__ for more information.
