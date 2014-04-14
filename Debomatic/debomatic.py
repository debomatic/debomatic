# Deb-o-Matic
#
# Copyright (C) 2007-2014 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

import os
from ConfigParser import ConfigParser
from argparse import ArgumentParser
from datetime import datetime
from daemon import DaemonContext, pidlockfile
from hashlib import sha256
from signal import signal, SIGINT, SIGTERM
from sys import stderr
from time import sleep

from build import FullBuild
from commands import Command
from modules import Module
from threadpool import ThreadPool


class Debomatic:

    def __init__(self):
        self.daemon = True
        self.log = Output()
        self.e = self.log.e
        self.w = self.log.w
        self.conffile = None
        self.configvers = '012a'
        self.opts = ConfigParser()
        self.rtopts = ConfigParser()
        parser = ArgumentParser()
        parser.add_argument('-c', '--configfile', metavar='file', type=str,
                            nargs=1, help='configuration file for Deb-o-Matic')
        parser.add_argument('-n', '--no-daemon', action='store_true',
                            help='do not launch Deb-o-Matic in daemon mode')
        parser.add_argument('-q', '--quit-process', action='store_true',
                            help='terminate Deb-o-Matic processes')
        args = parser.parse_args()
        if os.getuid():
            self.e(_('You must run Deb-o-Matic as root'))
        if args.configfile:
            self.conffile = args.configfile[0]
        if args.no_daemon:
            self.daemon = False
        self.default_options()
        self.packagedir = self.opts.get('default', 'packagedir')
        lock_sha = sha256()
        lock_sha.update(self.packagedir)
        self.lockfilepath = '/var/run/debomatic-' + lock_sha.hexdigest()
        self.lockfile = pidlockfile.PIDLockFile(self.lockfilepath)
        self.w(_('Lockfile is %s' % self.lockfilepath), 3)
        if args.quit_process:
            self.quit_process()
        if self.lockfile.is_locked():
            self.e(_('Another instance is running, aborting'))
        self.log.logverbosity = self.opts.getint('default', 'logverbosity')
        self.mod_sys = Module((self.log, self.opts,
                               self.rtopts, self.conffile))
        self.w(_('Startup hooks launched'), 2)
        self.mod_sys.execute_hook('on_start', {})
        self.w(_('Startup hooks finished'), 2)
        signal(SIGINT, self.quit)
        signal(SIGTERM, self.quit)
        if self.daemon:
            with open(self.opts.get('default', 'logfile'), 'a') as fd:
                with DaemonContext(pidfile=self.lockfile, stdout=fd, stderr=fd,
                                   signal_map={SIGTERM: self.quit}):
                    self.w(_('Entering daemon mode'), 2)
                    self.launcher()
        else:
            self.lockfile.acquire()
            self.launcher()

    def default_options(self):
        defaultoptions = ('builder', 'packagedir', 'configdir',
                          'architecture', 'maxbuilds', 'pbuilderhooks',
                          'inotify', 'sleep', 'logfile', 'logverbosity')
        if not self.conffile:
            self.e(_('Configuration file has not been specified'))
        if not os.path.exists(self.conffile):
            self.e(_('Configuration file %s does not exist') % self.conffile)
        self.opts.read(self.conffile)
        if (not self.opts.has_option('internals', 'configversion') or
                not self.opts.get('internals', 'configversion') ==
                self.configvers):
            self.e(_('Configuration file is not at version %s') %
                   self.configvers)
        for opt in defaultoptions:
            if (not self.opts.has_option('default', opt) or
                    not self.opts.get('default', opt)):
                self.e(_('Set "%(opt)s" in %(conffile)s') %
                       {'opt': opt, 'conffile': self.conffile})

    def launcher(self):
        self.pool = ThreadPool(self.log,
                               self.opts.getint('default', 'maxbuilds'))
        self.commandpool = ThreadPool(self.log, 1)
        self.queue_files()
        if self.opts.getint('default', 'inotify'):
            try:
                self.launcher_inotify()
            except ImportError:
                self.launcher_timer()
        else:
            self.launcher_timer()

    def launcher_inotify(self):
        import pyinotify

        class PE(pyinotify.ProcessEvent, Debomatic):

            def __init__(self, parent):
                self.parent = parent

            def process_IN_CLOSE_WRITE(self, event):
                if (event.name.endswith('.changes') or
                        event.name.endswith('commands')):
                    self.parent.queue_files([event.name])

        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, PE(self))
        wm.add_watch(self.packagedir, pyinotify.IN_CLOSE_WRITE)
        self.w(_('Inotify loop started'), 2)
        notifier.loop()

    def launcher_timer(self):
        self.w(_('Timer loop started'), 2)
        while True:
            sleep(self.opts.getint('default', 'sleep'))
            self.queue_files()

    def queue_files(self, filelist=None):
        if not filelist:
            try:
                filelist = os.listdir(self.packagedir)
            except OSError:
                self.lockfile.release()
                self.e(_('Unable to access %s directory') % self.packagedir)
        for filename in filelist:
            if filename.endswith('.changes'):
                b = FullBuild((self.opts, self.rtopts, self.conffile),
                              self.log, package=filename)
                if self.pool.add_task(b.run, filename):
                    self.w(_('Thread for %s scheduled' % filename), 2)
            elif filename.endswith('.commands'):
                c = Command((self.opts, self.rtopts, self.conffile),
                            self.log, self.pool, filename)
                if self.commandpool.add_task(c.process_command, filename):
                    self.w(_('Thread for %s scheduled' % filename), 2)

    def quit(self, signum, frame):
        self.w(_('Waiting for threads to complete...'))
        self.commandpool.wait_completion()
        self.pool.wait_completion()
        self.w(_('Shutdown hooks launched'), 2)
        self.mod_sys.execute_hook('on_quit', {})
        self.w(_('Shutdown hooks finished'), 2)
        if not self.daemon:
            self.lockfile.release()
        exit()

    def quit_process(self):
        if self.lockfile.is_locked():
            try:
                pid = pidlockfile.read_pid_from_pidfile(self.lockfilepath)
                try:
                    os.kill(pid, 0)
                except OSError:
                    pid = None
            except pidlockfile.PIDFileParseError:
                pid = None
            if pid:
                self.w(_('Waiting for threads to complete...'))
                os.kill(pid, SIGTERM)
                self.lockfile.acquire()
                self.lockfile.release()
            else:
                self.lockfile.break_lock()
                self.w(_('Obsolete lock removed'))
        exit()


class Output:

    def __init__(self):
        self.logverbosity = 1

    def w(self, msg, level=1):
        if self.logverbosity >= level:
            stderr.write('%s: %s\n' % (datetime.now().ctime(), msg))

    def e(self, msg):
        self.w(msg)
        exit()

    def t(self, msg):
        self.w(msg)
        raise RuntimeError
