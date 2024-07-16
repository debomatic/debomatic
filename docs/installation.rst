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

 *sudo python3 setup.py install*

If everything went smoothly, you should be able to launch debomatic from
your terminal's command line.

Installation of Git snapshots
-----------------------------

If you want to test bleeding-edge features, or want to be always up-to-date
with the latest and greatest Deb-o-Matic versions, you can download development
snapshots directly from upstream `Git`_ repository. Open a terminal and
launch the following command:

 *git clone https://github.com/debomatic/debomatic.git*

You can follow the instructions described in the `previous section`_ to install
Deb-o-Matic on your system.

.. Links
.. _Deb-o-Matic home page: https://debomatic.github.io/
.. _Deb-o-Matic download page: https://github.com/debomatic/debomatic/releases
.. _Git: https://github.com/debomatic/debomatic
.. _previous section: #installation-of-the-release-tarball

