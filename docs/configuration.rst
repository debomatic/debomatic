Configuration
=============

Configuration file
------------------

Deb-o-Matic configuration file is the most important file within Deb-o-Matic
infrastructure. It defines almost every option needed by Deb-o-Matic.
It is divided into five sections: ``debomatic``, which contains the general
options needed for Deb-o-Matic to work; ``distributions``, which contains all
the details related to the distributions Deb-o-Matic can build package for;
``chroots``, which contains the options related to the creation of the chroots
used to build packages; ``gpg``, which contains the options related to GPG
signature checking; ``modules``, which contains the options related to module
handling.

Other sections are optionally defined by each single module, their details will
be discussed in the :doc:`modules` section.

.. CAUTION::

 Configuration file must be formatted with `Python ConfigParser`_ syntax.

debomatic section
.................

This section is mandatory, Deb-o-Matic refuses to start if one of these
options is missing from the configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

* ``builduser``

 This option indicates the user Deb-o-Matic will build packages under.

 Suggested value: ``sbuild``

.. CAUTION::

 Make sure chosen user exists before launching Deb-o-Matic and is part of
 ``sbuild`` group, otherwise packages will not be built.

* ``incoming``

 This option indicates the directory where Deb-o-Matic expects to find source
 packages to build, and in which it will store chroots, build logs, and
 resulting packages.

 Suggested value: ``/incoming``

.. CAUTION::

 Make sure chosen directory exists before launching Deb-o-Matic, otherwise it
 will refuse to start.

* ``debootstrap``

 This option indicates which debootstrap tool is required to create the chroot
 to build source packages from. Deb-o-Matic currently supports debootstrap,
 cdebootstrap, and qemu-debootstrap.

 Suggested value: ``debootstrap``

.. CAUTION::

 Make sure chosen debootstrap utility is installed on your system, otherwise
 Deb-o-Matic will not be able to create chroots and build packages.

* ``architecture``

 This option indicates the architecture to build package for. To build packages
 for the same architecture of the running system, ``system`` can be used
 instead of specifying the exact one.

 Suggested value: ``system``

* ``threads``

 This option indicates the maximum concurrent builds that can be executed. If
 more build tasks are scheduled, they will be blocked until a slot becomes
 available again. More concurrent builds require more CPU cycles, so you may
 want to try different configurations to fit your needs.

 ``threads`` takes an integer as parameter.

 Suggested value: ``3``

* ``inotify``

 This option indicates whether to enable inotify support, or not. inotify will
 notify Deb-o-Matic about the availability of a new task, and will immediately
 start a new thread according to the requested task.

 If ``python3-pyinotify`` is not available, Deb-o-Matic will fall back to a
 timer-based method, where new tasks will be analyzed periodically.

 ``inotify`` takes True or False as parameter.

 Suggested value: ``True``

* ``sleep``

 This option indicates the number of seconds between two consecutive checks for
 new packages or commands to process. This option is only useful if inotify
 support is disabled, or is not available.

 ``sleep`` takes an integer as parameter.

 Suggested value: ``60``

* ``interval``

 This option indicates the number of seconds between two consecutive triggers
 for scheduled actions performed by modules.

 ``interval`` takes an integer as parameter.

 Suggested value: ``3600``

* ``logfile``

 This option indicates which file will be used to store information and warning
 messages issued by Deb-o-Matic during its execution.

 Suggested value: ``/var/log/debomatic.log``

* ``loglevel``

 This option indicates which kind of debug messages will be displayed. There
 are four levels: ``error``, ``warning``, ``info``, and ``debug``.

 Suggested value: ``info``

distributions section
.....................

This section is mandatory, Deb-o-Matic refuses to start if one of these
options is missing from the configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

* ``list``

 This option indicates the path of the distribution configuration file.
 More on those files will be discussed in the `Distributions file section`_.

 Suggested value: ``/etc/debomatic/distributions``

.. CAUTION::

 Make sure chosen directory exists before launching Deb-o-Matic, otherwise it
 will refuse to start.

* ``blacklist``

 This option indicates a list of distributions that are not allowed to accept
 new packages to build. Files targeted for a blacklisted distribution will be
 automatically deleted.

 Option must define a space-separated distribution names matching the ones
 listed in the `Distributions file section`_.

 Suggested value: ``(blank field)``

* ``mapper``

 This option indicates a list of distributions that, even if they are not
 defined by a distribution file (see `Distributions file section`_), can build
 packages on top of another distribution. This is particularly useful to
 indicate distribution aliases (such as ``sid <=> unstable``) or subsets
 (such as ``vivid-proposed => vivid``).

 Option must define a `Python dictionary`_ where keys are the distributions
 indicated by the packages, and values are the distributions on which build
 packages upon.

 Suggested value: ``{'sid': 'unstable'}``

chroots section
...............

This section is mandatory, Deb-o-Matic refuses to start if one of these
options is missing from the configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

* ``profile``

 This option indicates which schroot profile the chroots must adhere to.
 Profile files must be stored under ``/etc/schroot`` directory.

 Suggested value: ``debomatic`

.. CAUTION::

 Make sure chosen profile exists before launching Deb-o-Matic, otherwise 
 all chroots will not be created.

* ``commands``

 This option indicates the directory where sbuild commands are stored. Commands
 are executable scripts which are processed by sbuild during various build
 phases. Please refer to the sbuild (1) man page for additional details.

 At the moment, Deb-o-Matic provides a script to disable Internet connection
 within the chroot on Linux systems to avoid accessing remote resources during
 the build phase, and another one to increase the speed of unpacking of the 
 dependencies in the chroots.

 Suggested value: ``/usr/share/debomatic/sbuildcommands``

.. CAUTION::

 This directory needs to be bind mounted in the chroot for the scripts to
 be launched correctly. It is possible to do so by adjusting the schroot
 profile linked to the chroots used by Deb-o-Matic.

crossbuild section
..................

This section is optional, Deb-o-Matic will start normally if this section is
missing in the configuration file. Also, Deb-o-Matic needs to be restarted
to pick any change to one of these options.

* ``crossbuild``

 This option indicates whether to enable cross-build support, or not.

* ``hostarchitecture``

 This option indicates which host architecture to use when building source
 packages.

.. CAUTION::

 The architecture must have cross-compilation at compiler lever, otherwise
 it will not be possible to cross-compile source packages.

dpr section
...........

This section is optional, Deb-o-Matic will start normally if this section is
missing in the configuration file. Also, Deb-o-Matic needs to be restarted
to pick any change to one of these options.

* ``dpr``

 This option indicates whether to enable private repositories, or not.

 Suggested value: ``False``

* ``prefix``

 This option indicates the common prefix of all private repositories.

 Suggested value: ``dpr``

* ``repository``

 This option indicates the APT string of a local APT repository which is
 added at build time, useful in combination with the Repository module. The
 string must contain two ``%%(dist)s`` arguments which allows to specify
 dynamically the private repository name, for example:

 *deb http://debomatic.repository/debomatic/%%(dist)s %%(dist)s main*

gpg section
...........

This section is mandatory, Deb-o-Matic refuses to start if one of these
options is missing from the configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

``gnupg`` package is required for these options to be effective.

* ``gpg``

 This option indicates whether to enable signature checking support, or not. If
 enabled, Deb-o-Matic will delete unsigned files and files with signatures not
 available in its keyring.

 ``gpg`` takes True or False as parameter.

 Suggested value: ``False``

* ``keyring``

 This option indicates the gnupg keyring file in which Deb-o-Matic will look
 for valid and trusted GPG keys.

 Suggested value: ``/etc/debomatic/debomatic.gpg``

.. CAUTION::

 Make sure keyring file exists and is populated with trusted keys if GPG
 support is enabled, otherwise no tasks will be processed.

modules section
...............

This section is mandatory, Deb-o-Matic refuses to start if one of these
options is missing from the configuration file. Also, Deb-o-Matic needs to be
restarted to pick any change to one of these options.

More on modules handling will be discussed in the :doc:`modules` section.

* ``modules``

 This option indicates whether to enable module loading, or not.

 ``modules`` takes True or False as parameter.

 Suggested value: ``True``

* ``path``

 This option indicates the directory where Deb-o-Matic expects to find modules.
 Multiple directories can be listed, separated with a colon (``:``).

 Suggested value: ``/usr/share/debomatic/modules``

* ``threads``

 This option indicates how many modules Deb-o-Matic should launch in parallel.

 ``threads`` takes an integer as parameter.

 Suggested value: ``5``

* ``blacklist``

 This option indicates a list of modules that are not allowed to be executed
 during build process.

 Option must define a space-separated module names matching the ones listed in
 the :doc:`modules` section.

 Suggested value: ``AutoPkgTest Blhc Lintian Mailer Piuparts``

Distributions file
------------------

This file is populated by sections, each of them named after a distribution
to build packages for. Every section can define five options.

* ``suite``

 This option indicates the base suite to create the chroot for. Normally, it is
 equal to its distribution, but there are some exceptions (for instance,
 experimental's suite is unstable).

 This option is mandatory.

* ``mirror``

 This option indicates the mirror site which contains the primary package
 archive of the distribution.

 This option is mandatory.

* ``components``

 This option contains a space-delimited list of components to use.

 This option is mandatory.

* ``extramirrors``

 This option indicates additional mirrors to add in the chroot. More than one
 additional mirror can be defined, separated by a newline.

 This option is optional.

* ``extrapackages``

 This option contains a space-delimited list of additional packages to install
 in the chroot during its creation.

 This option is optional.

.. Links
.. _Python ConfigParser: http://docs.python.org/library/configparser.html
.. _Python dictionary: http://docs.python.org/library/stdtypes.html#mapping-types-dict
.. _Distributions file section: #distributions-file

