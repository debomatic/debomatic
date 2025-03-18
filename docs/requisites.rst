Requisites
==========

Build and installation requirements
-----------------------------------

In order to build and install Deb-o-Matic, the following packages are required:

* python3 (>= 3.9)

The following packages are required to install documentation and translations:

* python3-sphinx
* texlive-latex-base
* texlive-latex-recommended
* texlive-fonts-recommended
* texlive-latex-extra
* gettext
* latexmk

Runtime requirements
--------------------

In order to be able to run Deb-o-Matic, the following packages are required:

* python3 (>= 3.9)
* sbuild (>= 0.67.0-1)
* mmdebstrap

To enable additional features, you may want to install these packages:

* python3-pyinotify (>= 0.8.6)
* gpgv (>= 2.1)
* debian-archive-keyring
* ubuntu-archive-keyring or ubuntu-keyring
* lintian
* piuparts (>= 1.5.0)
* autopkgtest (>= 4.0)
* blhc
* devscripts
* apt-utils
* gnupg (>= 2.1)

An Internet connection is also required, broadband access is recommended
because underlying programs will fetch a lot of megabytes from remote locations
in order to create the chroots or satisfy build dependencies.

