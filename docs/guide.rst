===========
Deb-o-Matic
===========

--------------------------------------------------
Automatic build machine for Debian source packages
--------------------------------------------------

:Author: Luca Falavigna <dktrkranz@debian.org>
:Date: January 08, 2010
:Homepage: http://launchpad.net/debomatic

.. contents::

Introduction
============

This is Deb-o-Matic, an easy to use build machine for Debian-based source
packages. It provides a simple tool to automate building of Debian source
packages with limited user interaction and a straightforward configuration.

It has some useful feature such as automatic chroot update and automatic scan
and selection of source packages to build. It is meant to help developers to
build their packages without worrying too much of compilation, since it will
run in background and no user feedback is required during the whole process.

Requisites
==========

These packages are required to build and install Deb-o-Matic on your system:

* python (>= 2.5)
* python-docutils
* intltool

These ones are required to execute Deb-o-Matic:

* python (>= 2.5)
* pbuilder or cowbuilder
* debootstrap or cdebootstrap

To enable additional features, you may want to install these packages:

* python-pyinotify (>= 0.8.6)
* gnupg
* lintian

An Internet connection is also required, broadband access is recommended because
debootstrap will fetch several packages from the Internet to set up chroots.

Installation and removal
========================

Installation process is straightforward, just execute:

``python setup.py install``

You will find debomatic executable into /usr/bin, Debomatic module into
/usr/lib/python*/site-packages/Debomatic (or /usr/lib/python*/dist-packages/,
based on your Python version), custom modules in /usr/share/debomatic/modules
and related man pages into /usr/share/man directory.

Configuration
=============

In order to have Deb-o-Matic working, you have to prepare a configuration file
which will provide the options needed to run debomatic. You can look at
examples/debomatic.conf to see a working example.

The most important options are located under "default" section: here are some:

* packagedir: base directory where debomatic will scan for packages to build
* configdir: directory where pbuilder configuration files are stored
* maxbuilds: maximum number of parallel builds allowed 

See debomatic.conf man page for a complete list of the available options.

When main configuration file is complete, you must create the directories
referenced by packagedir and configdir, where you will put pbuilder
configuration files. Working examples are located into examples directory.
Names must match target distribution you want to build packages for (e.g. if
you want to build a package for unstable, pbuilder configuration filename must
be unstable). They should be the same as the ones provided by debootstrap.

See pbuilderrc man page for a complete list of the available options.

Running Deb-o-Matic
===================

To start Deb-o-Matic, you have to launch debomatic -c debomatic.conf command
(where debomatic.conf is your main configuration file). You need root
privileges to do so because of pbuilder infrastructure. This will start
debomatic in daemon mode, use -n switch to avoid this.

Now you can put source packages in the chosen package directory (identified by
packagedir option) and Deb-o-Matic will take care of the building phase.
Deb-o-Matic requires .changes files, be sure to generate a full Debian source
package by using a command such as dpkg-buildpackage -S -sa. You have to upload
.changes file and each file mentioned under its Files section. You may want to
use software like dput to automate the process.
A source upload is required, other type of .changes files could not be parsed
correctly leading to an ignored build.

Force pbuilder update
---------------------

Normally, Deb-o-Matic tries to update chroot only if there is a valid reason to
do so (e.g. if Release file on the preferred mirror changed, that means some
packages have been added or removed).

If your configuration has a local package repository, populated by packages
just built by Deb-o-Matic, you may always want to update pbuilder chroot. To do
so, simply put a file called "alwaysupdate" into gpg folder of the targets you
want to enable this feature for.

GPG support
-----------

Deb-o-Matic supports GPG-signed source packages to allow build for authorized
people only. To enable GPG support, you need to set options in "gpg" section in
main configuration file. Only packages signed with keys present in keyring
pointed by the correspondent option will be processed, unknown packages will be
deleted automatically.

How to prepare source packages
------------------------------

Deb-o-Matic can automatically fetch upstream tarballs if already available on
main distribution archive (e.g. http://archive.debian.com/debian), so you can
choose not to include them in such cases. You always need to include them in
case of new upstream version or new packages.

Modules
=======

Deb-o-Matic provides modules support. Modules are Python scripts pluggable at
runtime which extend Deb-o-Matic features. Available modules are stored into
modules directory. An example module can be found into examples directory,
useful to write your own Deb-o-Matic module.

Modules can be blacklisted to avoid launching them during build process.
A module.blacklist file needs to be defined in configuration file for this.
In order to define a blacklist, it is sufficient to list desired module name,
without trailing .py, separated by a space or a newline.

Bugs and feedback
=================

If you want to report a bug or a feature, please visit Deb-o-Matic homepage at
https://launchpad.net/debomatic.
