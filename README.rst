========
 getent
========

Python interface to the POSIX getent family of commands (getpwent, getgrent, getnetent, etc.)


Usage
=====

Here a few examples.

Load the interface::

    >>> import getent

Doing a passwd lookup::

    >>> print dict(getent.passwd('root'))
    {'dir': '/root',
     'gecos': 'root',
     'gid': 0,
     'name': 'root',
     'password': 'x',
     'shell': '/bin/bash',
     'uid': 0}

Doing a group lookup::

    >>> print dict(getent.group('root'))
    {'gid': 0, 'members': [], 'name': 'root', 'password': 'x'}


Bugs
====

Please use the `bug tracker at GitHub`_ for bugs or feature requests.

.. _bug tracker at GitHub: https://github.com/tehmaze/getent/issues


Authors
=======

* `Wijnand Modderman-Lenstra <https://maze.io/>`_
* Thomas Kula
* `Olivier Cortès <http://oliviercortes.com/>`_


Build status
============

.. image:: https://landscape.io/github/tehmaze/getent/master/landscape.svg
   :target: https://landscape.io/github/tehmaze/getent/master

.. image:: https://travis-ci.org/tehmaze/getent.svg
   :target: https://travis-ci.org/tehmaze/getent

.. image:: https://coveralls.io/repos/tehmaze/getent/badge.svg
   :target: https://coveralls.io/r/tehmaze/getent

