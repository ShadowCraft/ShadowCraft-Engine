ShadowCraft-Engine
==================

This repository contains the calculations engine behind the ShadowCraft
theorycrafting webapp for the Rogue class in World of Warcraft. For the
web application including the UI see
[shadowcraft-ui](https://github.com/cheald/shadowcraft-ui).

ShadowCraft-Engine is written in Python and supports both Python 2 and
3. The calculation modules can be found in shadowcraft/calcs. Objects
used for those calculations are defined in shadowcraft/objects.


How To
------

In order to support both Python 2 and 3, ShadowCraft-Engine depends on
the *future* library. For maths optimizations, we use *numpy*.
You can install everything by running:

```
pip install -r requirements.txt
```

To run a simple calculation for the rogue spec of your choice you can
look at the examples in the scripts folder. Feel free to play around
and edit those files as you see fit, when testing. E.g. to run a DPS
calculation for Subtlety, type:

```
python scripts/subtlety.py
```


Tests
-----

Although the tests currently do not provide good number testing for the
different specialization models, they can be used to ensure that nothing
major is broken. Run the tests using the following command:

```
python tests/runtests.py
```

Of course, we appreciate any help in extending the test coverage for the
engine.


Contributing
------------

The ShadowCraft team is always looking for help. If you would like to
contribute to the engine, you can always contact the active developers
or open a pull request on GitHub. There is also a #shadowcraft channel
on the [Ravenholdt Discord Server](https://discord.gg/DdPahJ9) that can
be used for discussion about the project.

Before writing code and submitting for review, please have a look at the
code style guidelines in style.md.
