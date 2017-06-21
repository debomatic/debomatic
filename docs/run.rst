Run Deb-o-Matic
===============

Launch Deb-o-Matic
------------------

Deb-o-Matic needs root privileges to be executed, otherwise it refuses to
start. In order to launch it, you can use the following command:

 *sudo debomatic -c debomatic.conf*

with ``debomatic.conf`` being the configuration file as described in the
:doc:`configuration` section. Make sure this file exists, otherwise Deb-o-Matic
will refuse to start.

Interactive mode
................

Deb-o-Matic will try to enter daemon mode automatically. If that is not
possible, Deb-o-Matic will be executed in interactive mode, and will be bound
to the shell that executed it, as a regular process.

It is also possible to force interactive mode by passing ``-i`` or
``--interactive`` option while invoking ``debomatic`` command:

 *sudo debomatic -c debomatic.conf -i*

This is particularly useful for debugging purposes.

Oneshot mode
............

Deb-o-Matic will try to build all files found in the ``incoming`` directory.
Alternatively, it is possible to attempt to build a single file by passing
``-o`` or ``--oneshot`` option while invoking ``debomatic`` command, following
by the file name of the package to build, which must be located in the
``incoming`` directory:

 *sudo debomatic -c debomatic.conf -o package_version_source.changes*

Stop Deb-o-Matic
----------------

In order to stop Deb-o-Matic, you should pass ``-q`` or ``--quit`` option to
``debomatic``:

 *sudo debomatic -c debomatic.conf -q*

Deb-o-Matic will not terminate child processes immediately, but will wait for
them to end first, so it could take a while to completely stop a Deb-o-Matic
instance.

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
 
Using systemctl command
-----------------------

If you installed Deb-o-Matic using Debian package, and your system does use of
systemd as default init, you could start, stop, and restart Deb-o-Matic with
the following commands, respectively:

 *sudo systemctl start debomatic*

 *sudo systemctl stop debomatic*

 *sudo systemctl restart debomatic*

systemd unit file is configured to look for ``/etc/debomatic/debomatic.conf``
as its default configuration file. You can change this path by providing a
systemd override file.

