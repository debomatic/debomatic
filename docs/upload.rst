Upload packages and commands
=======================

Prepare source packages
-----------------------

Deb-o-Matic will take into account both source only uploads and source and
binary uploads, while it will discard binary only uploads. Source only uploads
are recommended to avoid waste of bandwidth, so make sure you create packages
by passing ``-S`` flag to ``debuild`` or ``dpkg-buildpackage``.

Then, packages must be copied or uploaded into the directory specified by the
``incoming`` option in the configuration file to let Deb-o-Matic process
them.

In order to save bandwidth while uploading your packages, you could want to
avoid including upstream tarball in the .changes file if it is already
available in the distribution mirrors, Deb-o-Matic will fetch it automatically
for you. In order to do so, you have to pass ``-sd`` flag to ``debuild`` or
``dpkg-buildpackage``.

Multiple uploads of the same packages are allowed, Deb-o-Matic will overwrite
previous builds with new, fresh files.

User-defined fields
...................

sbuild uses several resolvers to determine and install build-dependencies
inside the chroots. Sometimes it is desirable to override the default resolver
to perform some advanced tasks (e.g. using a specific version of a package
which apt-based resolver cannot pick automatically.

In order to do so, you must define the ``XC-Debomatic-Resolver`` in the source
stanza of your ``control file``. For instance, if you want to use the aptitude
resolver, you must use the following syntax:

 *XC-Debomatic-Resolver: aptitude*

Prepare command files
---------------------

Deb-o-Matic provides an interface to perform specific tasks into the
Deb-o-Matic ``incoming`` directory such as removing uploaded files or
rebuilding packages. These operations are handled by commands stored in
``.commands`` files, and uploaded into Deb-o-Matic ``incoming`` directory by
using ``dcut`` utility, or by hand.

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
...............

It could happen some files are kept into Deb-o-Matic ``incoming`` directory,
and you would like to remove them. In order to do so, you must use the ``rm``
command:

 *echo "rm foo\*" > foo.commands*

where ``foo*`` is a regular expression matching the files you want to remove.

Rebuild packages
................

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
..............

You could want to prepare a porter upload, a binary-only upload which generates
architecture dependent binaries only. Additional information can be found in
`Debian Developer's Reference`_.

In order to do so, you must use the ``porter`` command:

 *echo "porter foo_version dist John Doe <jdoe@debian.org>" > foo.commands*

where foo is the name of the source package you want to rebuild, version is
the version of the package you want to rebuild, dist is the distribution which
rebuild package for, and the rest of the string is the address to be used as
maintainer field, which is usually the developer who is preparing the upload.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Binary NMU uploads
..................

You could want to prepare a binary NMU (or binNMU) upload, a binary-only upload
which generates architecture dependent binaries only, together with a
changelog entry describing why the upload was needed. Additional information
can be found in `Debian Developer's Reference`_.

In order to do so, you must use the ``binnmu`` command:

 *echo "binnmu foo_version dist binNMU_version \"changelog\"
  John Doe <jdoe@debian.org>" > foo.commands*

where foo is the name of the source package you want to rebuild, version is
the version of the package you want to rebuild, dist is the distribution which
rebuild package for, binNMU_version is the progressive binNMU number, changelog
is the reason why the upload was prepared (enclosed in quotation marks), and
the rest of the string is the address to be used as maintainer field, which is
usually the developer who is preparing the upload.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Rebuild packages with extra build-dependencies
..............................................

You could want to rebuild a package already in the mirrors also adding a
specific build-dependency to see whether it compiles with a newer library
version. In order to do so, you must use the ``builddep`` command:

 *echo "builddep foo_version dist extrapackage (>= packageversion)"*
 *> foo.commands*

where ``extrapackage`` is the name of the package you want to install before
the compilation takes place, and ``packageversion`` is the optional version of
the package you want to install. More than one package can be defined,
separated by commas.

.. CAUTION::

 Make sure packages are available in the distribution mirrors, otherwise they
 cannot be downloaded and processed by Deb-o-Matic.

Killing builds
..............

You could want to terminate a build you erroneously uploaded, or you do not
want it to complete to avoid wasting too many resources.

In order to do so, you must use the ``kill`` command:

 *echo "kill foo_version dist " > foo.commands*

where foo is the name of the source package you want to terminate its build,
version is its version, and dist is the distribution the package is being
built for.

.. Links
.. _Debian Developer's Reference: https://www.debian.org/doc/manuals/developers-reference/pkgs.html#porter-guidelines
