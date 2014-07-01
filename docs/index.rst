===========
Deb-o-Matic
===========

What is Deb-o-Matic?
====================

Deb-o-Matic is an easy to use utility to build Debian source packages, meant
to help developers to automate the building of their packages with a tool that
requires limited user interaction and a simple configuration.

It provides some useful features such as automatic chroot update, rebuild of
source packages, post-build checks, and much more. It is also extendable with
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
with pbuilder and long builds. Some of them still use Deb-o-Matic to build
their packages.

Over time, Deb-o-Matic has been used by some FLOSS projects too. For example,
Scilab Enterprises uses Deb-o-Matic to build Scilab in a transparent and
automatic way. Every 5 minutes, a cronjob checks if any new commit happened and
start a built process through Deb-o-Matic.

Requisites
==========

Build and installation requirements
-----------------------------------

In order to build and install Deb-o-Matic, the following packages are required:

* python3 (>= 3.2)

The following packages are required to install documentation and translations:

* python3-sphinx
* texlive-latex-base
* texlive-latex-recommended
* texlive-fonts-recommended
* texlive-latex-extra
* gettext

Runtime requirements
--------------------

In order to be able to run Deb-o-Matic, the following packages are required:

* python3 (>= 3.2)
* pbuilder or cowbuilder
* debootstrap or cdebootstrap

To enable additional features, you may want to install these packages:

* python3-pyinotify (>= 0.8.6)
* gpgv
* gnupg
* lintian
* piuparts (>= 0.45)
* debian-archive-keyring and/or ubuntu-keyring

An Internet connection is also required, broadband access is recommended
because underlying programs will fetch a lot of megabytes from remote locations
in order to create the chroots or satisfy build dependencies.

Installation
============

Installation from Debian/Ubuntu repository
------------------------------------------

Deb-o-Matic is available in Debian and Ubuntu repositories, so you can launch
the following command to install Deb-o-Matic on your system:

 *sudo apt-get install debomatic*

Depending on your Debian or Ubuntu release, you could not have the latest
version. It is usually suggested to use the latest one to obtain new features
and bugfixes. You may want to check `Deb-o-Matic home page`_ from time to time
to see whether a new release is available.

Installation of the release tarball
-----------------------------------

If the version in Debian/Ubuntu repositories is not the one you are looking
for, you can download a release tarball from `Deb-o-Matic download page`_.

Unpack the release tarball, enter the new created directory, and launch the
following command:

 *sudo python setup.py install*

If everything went smoothly, you should be able to launch debomatic from
your terminal's command line.

Installation of Bazaar snapshots
--------------------------------

If you want to test bleeding-edge features, or want to be always up-to-date
with latest and greatest Deb-o-Matic versions, you can download development
snapshots directly from upstream `Bazaar`_ repository. Open a terminal and
launch the following command:

 *bzr branch lp:debomatic*

You can follow the instructions described in the `previous section`_ to install
Deb-o-Matic on your system.

Configuration
=============

Configuration file
------------------

Deb-o-Matic configuration file is the most important file within Deb-o-Matic
infrastructure. It defines almost every option needed by Deb-o-Matic.
It is divided into five sections: ``default``, which contains the mandatory
options needed for Deb-o-Matic to work; ``runtime``, which contains the options
related to parameters which can be modified at runtime; ``gpg``, which contains
the options related to gpg signature checking; ``modules``, which contains the
options related to module handling; ``internals``, which contains options
related to Deb-o-Matic implementation details.

.. CAUTION::

 Configuration file must be formatted with `Python ConfigParser`_ syntax.

default section
...............

These options are mandatory, Deb-o-Matic refuses to start if one of these
options is missing from configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

* ``builder``

 This option indicates which builder tool is required to perform building of
 the source packages. Deb-o-Matic currently supports pbuilder and cowbuilder.
 cowbuilder is usually faster, but requires more disk space for its chroots.

 Suggested value: ``pbuilder``

.. CAUTION::

 Make sure chosen builder is installed on your system, otherwise Deb-o-Matic
 will not be able to create chroots and build packages.

* ``debootstrap``

 This option indicates which debootstrap tool is required to create the chroot
 to build source packags from. Deb-o-Matic currently supports debootstrap,
 cdebootstrap, and qemu-debootstrap.

 Suggested value: ``debootstrap``

.. CAUTION::

 Make sure chosen debootstrap is installed on your system, otherwise Deb-o-Matic
 will not be able to create chroots and build packages.

* ``packagedir``

 This option indicates the directory where Deb-o-Matic expects to find source
 packages to build, and in which it will save chroots, build logs, and
 resulting packages.

 Suggested value: ``/incoming``

.. CAUTION::

 Make sure chosen directory exists before launching Deb-o-Matic, otherwise it
 will refuse to start.

* ``configdir``

 This option indicates the directory where distribution configuration files are
 stored. More on those files will be discussed in the
 `Distribution files section`_.

 Suggested value: ``/etc/debomatic/distributions``

.. CAUTION::

 Make sure chosen directory exists before launching Deb-o-Matic, otherwise it
 will not be able to build any package.

* ``architecture``

 This option indicates the architecture to build package for. To build
 packages for the same architecture of the running system, ``system``
 can be used instead of specifying the exact one.

 Suggested value: ``system``

* ``pbuilderhooks``

 This option indicates the directory where pbuilder hooks are stored. Hooks
 are executable scripts which are processed by pbuilder and cowbuilder during
 various build phases. Please refer to the pbuilder (8) man page for additional
 details about pbuilder hooks.

 At the moment, Deb-o-Matic provides scripts to disable Internet connection
 within the chroot on Linux systems to avoid accessing remote resources during
 the build phase.

 Suggested value: ``/usr/share/debomatic/pbuilderhooks``

.. CAUTION::

 In order to disable pbuilder hooks, you have to declare an existing, empty
 directory in pbuilderhooks option.

* ``maxbuilds``

 This option indicates the maximum concurrent builds that can be executed. If
 more build tasks are scheduled, they will be blocked until a slot becomes
 available again. More concurrent builds require more CPU cycles and disk
 space, so you may want to try different configurations to fit your needs.

 ``maxbuilds`` takes an integer as parameter.

 Suggested value: ``3``

* ``inotify``

 This option indicates whether to enable inotify support or not. inotify will
 notify Deb-o-Matic about the availability of a new task, and will immediately
 start a new thread according to the requested task.

 If ``python-pyinotify`` is not available, Deb-o-Matic will fall back to a
 timer-based method.

 ``inotify`` takes 1 or 0 as parameter.

 Suggested value: ``1``

* ``sleep``

 This option indicates the number of seconds between two consecutive checks for
 new packages or commands to process. This option is only useful if inotify
 support is disabled or is not available.

 ``sleep`` takes an integer as parameter.

 Suggested value: ``60``

* ``logfile``

 This option indicates which file will be used to store information and warning
 messages issued by Deb-o-Matic during its execution.

 Suggested value: ``/var/log/debomatic.log``

* ``loglevel``

 This option indicates which kind of debug messages will be displayed. There
 are four levels: ``error``, ``warning``, ``info``, and ``debug``.

 Suggested value: ``info``

gpg section
...........

These options are not mandatory, Deb-o-Matic will check whether they are
defined in the configuration file before trying to use related features. Also,
Deb-o-Matic needs to be restarted to pick any change to one of these options.

``gnupg`` package is required for these options to be effective.

* ``gpg``

 This option indicates whether to enable signature checking support or not. If
 enabled, Deb-o-Matic will delete unsigned files and files with signatures not
 available in its keyring.

 ``gpg`` takes 1 or 0 as parameter.

 Suggested value: ``0``

* ``keyring``

 This option indicates the gnupg keyring file in which Deb-o-Matic will look
 for allowed and identified GPG signatures.

 Suggested value: ``/etc/debomatic/debomatic.gpg``

.. CAUTION::

 Make sure keyring file exists and is populated with allowed signatures if GPG
 support is enabled, otherwise no tasks will be processed.

modules section
...............

These options are not mandatory, Deb-o-Matic will check whether they are
defined in the configuration file before trying to use related features. Also,
Deb-o-Matic needs to be restarted to pick any change to one of these options.

More on modules handling will be discussed in the `Modules section`_.

* ``modules``

 This option indicates whether to enable module loading or not.

 Suggested value: ``1``

* ``modulespath``

 This option indicates the directory where Deb-o-Matic expects to find modules.

 Suggested value: ``/usr/share/debomatic/modules``

* ``maxthreads``

 This option indicates how many modules Deb-o-Matic should launch in parallel.

 Suggested value: ``5``

runtime section
...............

These options are not mandatory, Deb-o-Matic will check whether they are
defined in the configuration file before trying to use related features. As the
section name suggests, these options can be adjusted at runtime, Deb-o-Matic
will pick the updated value during the build process.

* ``alwaysupdate``

 This option indicates a list of distributions for which their chroots have to
 be updated before every build, even if repository's Release file has not
 changed.

 Option must define a space-separated distribution names matching the ones
 listed in the `Distribution files section`_.

 Suggested value: ``unstable experimental raring``

* ``distblacklist``

 This option indicates a list of distributions that are not allowed to accept
 new packages to build. Files targeted for a blacklisted distribution will be
 automatically deleted.

 Option must define a space-separated distribution names matching the ones
 listed in the `Distribution files section`_.

 Suggested value: ``(blank field)``

* ``modulesblacklist``

 This option indicates a list of modules that are not allowed to be executed
 during build process.

 Option must define a space-separated module names matching the ones listed in
 the `Modules section`_.

 More on module handling will be discussed in the `Modules section`_.

 Suggested value: ``Lintian Mailer Piuparts``

* ``mapper``

 This option indicates a list of distributions that, even if they are not
 defined by a distribution file (see `Distribution files section`_), can build
 packages on top of another distribution. This is particularly useful to
 indicate distribution aliases (such as ``sid <=> unstable``) or subsets
 (such as ``oneiric-proposed => oneiric``).

 Option must define a `Python dictionary`_ where keys are the distributions
 indicated by the packages, and values are the distributions on which build
 packages upon.

 Suggested value: ``{'sid': 'unstable'}``

internals section
.................

These options are mandatory, Deb-o-Matic refuses to start if one of these
options is missing from configuration file. Also, these options should not be
modified, and must follow this guide thoroughly.

* ``configversion``

 This option indicates which version of the configuration file Deb-o-Matic
 expects to find. If it does not match the one needed by Deb-o-Matic, it
 refuses to start.

 This option must be set to ``013a``

Distribution files
------------------

These files are pbuilder configuration files that define the basic settings of
a pbuilder environment to build packages upon. A comprehensive list of the
options that can be defined can be found in the ``pbuilderrc (5) man page``.

Here are the mandatory options Deb-o-Matic will check for their existence:

* ``DISTRIBUTION``: indicates the default distribution to use.
* ``MIRRORSITE``: indicates the mirror site which contains the package archive.
* ``COMPONENTS``: space-delimited list of distribution components to use.
* ``DEBOOTSTRAP``: indicates which implementation of debootstrap to use.

Run Deb-o-Matic
===============

Launch Deb-o-Matic
------------------

Deb-o-Matic needs root privileges to be executed, otherwise it refuses to
start. In order to launch it, you can use the following command:

 *sudo debomatic -c debomatic.conf*

with ``debomatic.conf`` being the configuration file as described in the
`Configuration section`_. Make sure this file exists, otherwise Deb-o-Matic
will refuse to start.

Interactive mode
................

Deb-o-Matic will try to enter daemon mode automatically. If that is not
possible (e.g. ``python-daemon`` package is not installed), Deb-o-Matic will
be executed in interactive mode, and will be bound to the shell that launched
it, as a regular process.

It is also possible to force interactive mode by passing ``-n`` or
``--nodaemon`` option while invoking ``debomatic`` command:

 *sudo debomatic -c debomatic.conf -n*

This is particularly useful for debugging purposes.

Stop Deb-o-Matic
----------------

In order to stop Deb-o-Matic, you should pass ``q`` or ``--quit-process``
options to ``debomatic``:

 *sudo debomatic -c debomatic.conf -q*

Deb-o-Matic will not terminate child processes, but will wait for them to end
first, so it could take a while to completely stop Deb-o-Matic instance.

.. CAUTION::

 Deb-o-Matic uses a rather strong locking mechanism, so it is not recommended
 to terminate debomatic process with ``kill`` command.

Using service command
---------------------

If you installed Deb-o-Matic using Debian package, you could start, stop, and
restart Deb-o-Matic with the following commands, respectively:

 *sudo service debomatic start*

 *sudo service debomatic stop*

 *sudo service debomatic restart*

You will need to adjust configuration stored in ``/etc/default/debomatic`` file
to manage Deb-o-Matic with this method, though. In particular, you will have to
set ``DEBOMATIC_AUTOSTART`` variable to 1.

Service configuration
.....................

In order to start Deb-o-Matic with ``service`` command, you must adjust some
parameters defined in ``/etc/default/debomatic`` file.

* ``DEBOMATIC_AUTOSTART``

 This option indicates whether to execute Deb-o-Matic at system boot. Default
 value is set to ``0`` to avoid accidental executions without a sane
 configuration. It must be set to ``1`` in order to launch Deb-o-Matic.

* ``DEBOMATIC_CONFIG_FILE``

 This option indicates the configuration file Deb-o-Matic is going to use.

* ``DEBOMATIC_OPTS``

 This option allows to pass extra options to Deb-o-Matic.

Prepare source packages
=======================

Deb-o-Matic will take into account both source only uploads and source plus
binary uploads, while it will discard binary only uploads. Source only uploads
are recommended to avoid waste of bandwith, so make sure you create packages by
passing ``-S`` flag to ``debuild`` or ``dpkg-buildpackage``.

Then, packages must be copied or uploaded into the directory specified by
``packagedir`` option in the configuration file to let Deb-o-Matic process
them.

In order to save bandwidth while uploading your packages, you could want to
avoid including upstream tarball in the .changes file if it is already
available in the distribution mirrors, Deb-o-Matic will fetch it automatically
for you. In order to do so, you have to pass ``-sd`` flag to ``debuild`` or
``dpkg-buildpackage``.

Multiple uploads of the same packages are allowed, Deb-o-Matic will overwrite
previous builds with new, fresh files.

Prepare command files
=====================

Deb-o-Matic provides an interface to perform specific tasks into the
Deb-o-Matic ``packagedir`` directory such as removing uploaded files or
rebuilding packages. These operations are handled by commands stored in
``.commands`` files, and uploaded into Deb-o-Matic ``packagedir`` by using
``dcut`` utility, or by hand.

Using dcut is usually simpler, just launch the following command:

 *dcut -U mydebomatic commandfile.commands*

where ``mydebomatic`` is a dput host as described in dput.cf (5) man page, and
``commandfile.commands`` is the file containing the commands to be executed by
Deb-o-Matic.

Multiple commands can be stored in a single ``.commands`` file, but it is
usually safer to issue a single command per file.

.. CAUTION::

 If signature checking support is enabled, .commands files must be signed by a
 known key, otherwise they will be deleted and no action will be taken.

Remove packages
---------------

It could happen some files are kept into Deb-o-Matic ``packagedir`` and you
need to remove them. In order to do so, you must use the ``rm`` command:

 *echo "rm foo\*" > foo.commands*

where ``foo*`` is a regular expression matching the files you want to remove.

Rebuild packages
----------------

You could want to rebuild a package already in the mirrors to see whether it
compiles with newer packages, to analyze its content, and so on. In order to do
so, you must use the ``rebuild`` command:

 *echo "rebuild foo_version dist" > foo.commands*

where ``foo`` is the name of the source package you want to rebuild,
``version`` is the version of the package you want to rebuild, and ``dist`` is
the distribution which rebuild the package for.

Deb-o-Matic can also rebuild packages available in other distributions. The
syntax is similar, you just have to indicate which distribution to pick
packages from:

 *echo "rebuild foo_version dist origin" > foo.commands*

where ``origin`` is the distribution to pick packages from.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Porter uploads
--------------

You could want to prepare a porter upload, a binary-only upload which generates
architecture dependent binaries only. Additional information can be found in
`Debian Developer's Reference`_.

In order to do so, you must use the ``porter`` command:

 *echo "porter foo_version dist Joe Doe <j.doe@acme.com>" > foo.commands*

where foo is the name of the source package you want to rebuild, version is
the version of the package you want to rebuild, dist is the distribution which
rebuild package for, and the element between quotes is the address to be used
as maintainer field, which is usually the developer who is preparing the
upload.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Rebuild packages with extra build-dependencies
----------------------------------------------

You could want to rebuild a package already in the mirrors also adding a
specific build-dependency to see whether it compiles with a newer library
version. In order to do so, you must use the ``builddep`` command:

 *echo "builddep foo_version dist extrapackage=packageversion" > foo.commands*

where ``extrapackage`` is the name of the package you want to install before
the compilation takes place, and ``packageversion`` is the optional version of
the package you want to install.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Modules
=======

Contents
--------

This module scans binary packages and stores their content in a ``.contents``
file created in the same directory of the resulting files.

In order for this module to work properly, ``debc`` tool from ``devscripts``
must be available.

DateStamp
---------

This module displays timestamps of when a package started to build, when it
finished, and the build elapsed time. Timestamps are stored in a ``.datestamp``
file created in the same directory of the resultinf files.

Lintian
-------

This module allows lintian to be executed, checking the built packages for
errors and warnings, and creates a report in the same directory of the
resulting files.

In order for this module to work properly, ``lintian`` package must be
installed.

Parameters
..........

* ``lintopts``

This option indicates the extra options to pass to lintian.

 Suggested value: ``-iIE --pedantic``

Mailer
------

This module allows to send emails about the status of the builds. Body of the
email will contain an excerpt of the build log to easily see failures or
potential problems.

.. CAUTION::

 Make sure signature checking support is enabled before trying to use this
 module, otherwise it will not work as it relies on the address provided in
 the GPG key to obtain the email address to send messages to.

Parameters
..........

* ``fromaddr``

This option indicates the email address used to send the emails from.

* ``smtphost``

This option indicates the SMTP server used to send the emails.

* ``smtpport``

This option indicates the SMTP port on which the SMTP server listens to.

* ``tls``

This option indicates whether to enable TLS mode or not.

* ``authrequired``

This option indicates whether the SMTP server requires authentication or not.

* ``smtpuser``

This option indicates the user name to be passed to the SMTP server.

* ``smtppass``

This option indicates the password to be passed to the SMTP server.

* ``success``

This option indicates the template to be used to report successful builds.

* ``failure``

This option indicates the template to be used to report failed builds.

* ``lintlog``

This option indicates whether the lintian log is to be attached after the build
log or not.

Piuparts
--------

This module allows piuparts to be executed, checking the built packages for
potential problems, and creates a report in the same directory of the
resulting files.

In order for this module to work properly, ``piuparts`` package must be
installed.

Parameters
..........

* ``piupopts``

This option indicates the extra options to pass to piuparts.

 Suggested value: ``--log-level=info``

Blhc
----

This module allows blhc to be executed, checking the build log of built packages
for missing hardening flags.

In order for this module to work properly, ``blhc`` package must be installed.

Parameters
----------

* ``blhcopts``

This option indicates the extra options to pass to blhc.

 Suggested value: ``--all``

PrevBuildCleaner
----------------

This modules deletes obsolete files created during previous builds to avoid
picking obsolete files by mistake. It currently deletes these files:

* \*.deb
* \*.ddeb
* \*.gz
* \*.bz2
* \*.xz
* \*.dsc
* \*.contents
* \*.lintian
* \*.changes

Repository
----------

This module allows the creation of a simple repository of Debian binary
packages, which is refreshed each time a build is performed, allowing to build
packages build-depending on previously built ones. In order for this module to
work properly, ``apt-ftparchive`` tool from ``apt-utils`` package must be
available.

Parameters
..........

* ``gpgkey``

This option indicates the GPG ID used to sign the Release file of the
repository.

* ``pubring``

This option indicates the path where to look for the public GPG key used to
sign the Release file of the repository.

* ``secring``

This option indicates the path where to look for the private GPG key used to
sign the Release file of the repository.

.. Links
.. _Canonical's PPAs: http://www.ubuntu.com/news/launchpad-ppa
.. _wanna-build: http://git.debian.org/?p=mirror/wanna-build.git;a=summary
.. _Deb-o-Matic home page: https://launchpad.net/debomatic
.. _Deb-o-Matic download page: https://launchpad.net/debomatic/+download
.. _Bazaar: https://code.launchpad.net/~dktrkranz/debomatic/debomatic.dev
.. _previous section: #installation-of-the-release-tarball
.. _Python ConfigParser: http://docs.python.org/library/configparser.html
.. _Python dictionary: http://docs.python.org/library/stdtypes.html#mapping-types-dict
.. _Distribution files section: #distribution-files
.. _Modules section: #modules
.. _Configuration section: #configuration
.. _Debian Developer's Reference: http://www.debian.org/doc/manuals/developers-reference/pkgs.html#porter-guidelines
