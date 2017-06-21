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
* sbuild (>= 0.67.0-1)
* schroot (>= 1.6.10-2)
* debootstrap, cdebootstrap, or qemu-debootstrap
* python3-toposort

To enable additional features, you may want to install these packages:

* python3-pyinotify (>= 0.8.6)
* gpgv
* debian-archive-keyring
* ubuntu-archive-keyring or ubuntu-keyring
* lintian
* piuparts (>= 0.45)
* autopkgtest (>= 4.0)
* blhc
* devscripts
* apt-utils
* gnupg

An Internet connection is also required, broadband access is recommended
because underlying programs will fetch a lot of megabytes from remote locations
in order to create the chroots or satisfy build dependencies.

