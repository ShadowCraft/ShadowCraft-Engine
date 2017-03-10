Style Guideines for ShadowCraft-Engine
======================================

These are the code style guidelines that were defined by Aldriana when the
project started. Although, they may or may not have been heeded consistently
throughout the code base, try to keep them in mind when writing new code.

1. Indents are 4 spaces. Tabs are strictly forbidden.

2. Avoid trailing whitespace in all cases. And I do mean all cases.

3. Line length: Try to keep comments to 80 characters. For general code I'm
   not going to enforce a strict limit, but if you're going over 120 characters
   or so you should think about whether there's a natural way to break it. If
   there's not, that's fine, but if there is, that's better.

4. List comprehensions, lambda functions, map(), reduce(), filter(), etc. are
   all fine if they're simple and generally aid code clarity. If you're doing
   some hairy nested thing, it's probably better to split it up.

5. For binary operators (+, -, *, /, %, etc.) put a space around the operator:

   Correct: `a = 1 + 2 * 3`

   Wrong: `a=1+2*3`

   Exception: When assigning a default value for a function parameter, do not
   use spaces:

   Correct: `def foo(bar=1):`

   Wrong: `def foo(bar = 1):`

6. Imports: With the exception of importing something that's in `__init__`,
   import the module, not the class.

   Correct: `from calcs import gylphs`

   Slightly Wrong: `import calcs.glyphs`

   Wrong: `from calcs.glyphs import Glyph`

   Very Wrong: `from calcs.glyph import *`

   Imports should also generally be done in alphabetical order.

7. Try to keep module names distinct to the extent that it's possible to do so
   and still have them make sense. It helps if you use descriptive module
   names.

8. Modules names should be lowercase_and_underscores.

9. Function names should be lowercase_and_underscores.

10. Class names should be CamelCase.

11. If a module primarily consists of a single class definition, the module
    name and the class name should match.

12. Any string where there is even the slightest chance it will be shown to an
    external user should use named introspection for variables. This is to
    make translation, um, possible.

    Correct: `"%(character_name)s is level %(character_level)d" % {'character_name': name, 'character_level': level}`

    Wrong: `"%s is level %d" % (name, level)`

    Very Wrong: `name + ' is level ' + str(level)`

    To explain: in various languages the sentence syntax may require the
    variables to be in a different order. Giving them good descriptive names
    lets the translators properly rearrange them as needed to convey the proper
    meaning.

13. Comments are a good thing. If what you're doing isn't immediately obvious
    from a quick readthrough, add a comment to explain it. Recommended practise
    are comments without a space after the #.

In general: please try to write code that's as readable and maintainable as
possible. You only write the code once, but it will be read many many times.
Hence it's worth spending an extra couple of minutes writing it if it saves the
readers even a few seconds in understanding it. As the saying goes: always
write code as though the person who has to maintain it is a dangerous
psychopath that knows where you live.
