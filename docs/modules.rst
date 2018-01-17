Modules
=======

Autopkgtest
-----------

This module allows adt-run to be executed if source package declares a
Testsuite against autopkgtest. It creates a report in the same directory of the
resulting files.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``autopkgtest`` section. Make sure
 you create it in your configuration file.

* ``options``

This option indicates the extra options to pass to adt-run.

 Suggested value: ``--no-built-binaries``

Blhc
----

This module allows blhc to be executed, checking the build log of built
packages for missing hardening flags.

In order for this module to work properly, ``blhc`` package must be installed.

Parameters
----------

.. CAUTION::

 These parameters must be listed under the ``blhc`` section. Make sure you
 create it in your configuration file.

* ``options``

This option indicates the extra options to pass to blhc.

 Suggested value: ``--all``

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

.. CAUTION::

 These parameters must be listed under the ``lintian`` section. Make sure you
 create it in your configuration file.

* ``options``

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

.. CAUTION::

 These parameters must be listed under the ``mailer`` section. Make sure you
 create it in your configuration file.

* ``sender``

This option indicates the email address used to send the emails from.

* ``server``

This option indicates the SMTP server used to send the emails.

* ``port``

This option indicates the SMTP port on which the SMTP server listens to.

* ``tls``

This option indicates whether to enable TLS mode, or not.

* ``authrequired``

This option indicates whether the SMTP server requires authentication, or not.

* ``user``

This option indicates the user name to be passed to the SMTP server.

* ``pass``

This option indicates the password to be passed to the SMTP server.

* ``success``

This option indicates the template to be used to report successful builds.

* ``failure``

This option indicates the template to be used to report failed builds.

* ``lintian``

This option indicates whether the lintian log is to be attached after the build
log, or not.

Piuparts
--------

This module allows piuparts to be executed, checking the built packages for
potential problems, and creates a report in the same directory of the
resulting files.

In order for this module to work properly, ``piuparts`` package must be
installed.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``piuparts`` section. Make sure you
 create it in your configuration file.

* ``options``

This option indicates the extra options to pass to piuparts.

 Suggested value: ``--log-level=info``

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
* \*.build
* \*.contents
* \*.lintian
* \*.piuparts
* \*.changes
* \*.autopkgtest
* \*.bhlc

RemoveChroots
-------------

This module allows to remove chroots after a certain amount of days.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``removechroots`` section. Make
 sure you create it in your configuration file.

* ``days``

This option indicates the number of days after which chroots are removed.

RemovePackages
--------------

This module allows to remove built packages after a certain amount of days.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``removepackages`` section. Make
 sure you create it in your configuration file.

* ``days``

This option indicates the number of days after which build packages are
removed from the pool directory.

Repository
----------

This module allows the creation of a simple repository of Debian binary
packages, which is refreshed each time a build is performed, allowing to build
packages build-depending on previously built ones. In order for this module to
work properly, ``apt-ftparchive`` tool from ``apt-utils`` package must be
available.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``repository`` section. Make sure
 you create it in your configuration file.

* ``gpgkey``

This option indicates the GPG ID used to sign the Release file of the
repository.

* ``pubring``

This option indicates the path where to look for the public GPG key used to
sign the Release file of the repository.

* ``secring``

This option indicates the path where to look for the private GPG key used to
sign the Release file of the repository.

SourceUpload
------------

This module allows the creation of a .sourceupload.changes file to be used to
upload source-only uploads to the Debian archive.

UpdateChroots
-------------

This module allows to update chroots after a certain amount of days.

Parameters
..........

.. CAUTION::

 These parameters must be listed under the ``updatechroots`` section. Make
 sure you create it in your configuration file.

* ``days``

This option indicates the number of days after which chroots are updated.
