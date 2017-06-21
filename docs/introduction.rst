Introduction
============

What is Deb-o-Matic?
---------------------

Deb-o-Matic is an easy to use utility to build Debian source packages, meant
to help developers to automate the building of their packages with a tool that
requires limited user interaction and a simple configuration.

It provides some useful features such as automatic chroot creation, rebuild of
source packages, post-build checks, and much more. It is also extendible with
modules that are loaded and executed during the build phases.

Why Deb-o-Matic?
----------------

When the author started to contribute to the Debian and Ubuntu development, he
was running a 10-year-old PC and had a poor network connectivity. Downloading
lots of packages had always been a nightmare, `Canonical's PPAs`_ were always
busy compiling other packages because of the limited resources invested at the
time, and `wanna-build`_ was (and still is) too complex to set up for
relatively simple workflows.

A brand new software was created to help building source packages to avoid the
burden of the compilation, without wasting too much time configuring complex
softwares to work. Deb-o-Matic was born! A group of Debian and Ubuntu
developers started to use it as their primary build machine to avoid playing
with sbuild and long builds. Some of them still use Deb-o-Matic to build
their packages.

Over time, Deb-o-Matic has been used by some FLOSS projects too. For example,
Scilab Enterprises uses Deb-o-Matic to build Scilab in a transparent and
automatic way. Every 5 minutes, a cronjob checks if any new commit happened and
start a built process through Deb-o-Matic.

.. Links
.. _Canonical's PPAs: https://help.launchpad.net/Packaging/PPA
.. _wanna-build: https://anonscm.debian.org/cgit/mirror/wanna-build.git/

