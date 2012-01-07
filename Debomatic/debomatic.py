# Deb-o-Matic
#
# Copyright (C) 2007-2011 Luca Falavigna
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
from datetime import datetime
from getopt import getopt, GetoptError
from daemon import DaemonContext
from daemon.pidlockfile import PIDLockFile
from signal import signal, SIGINT
from sys import argv, stderr
from time import sleep

from build import FullBuild
from commands import Command
from modules import Module
from threadpool import ThreadPool


class Debomatic:

    def __init__(self):
        daemon = True
        self.log = Output()
        self.e = self.log.e
        self.w = self.log.w
        self.conffile = None
        self.lockfile = PIDLockFile('/var/run/debomatic')
        self.opts = ConfigParser()
        if os.getuid():
            self.e(_('You must run deb-o-matic as root'))
        try:
            opts, args = getopt(argv[1:], 'c:n', ['config=', 'nodaemon'])
        except GetoptError as error:
            self.e(error.msg)
        for o, a in opts:
            if o in ('-c', '--config'):
                self.conffile = a
            if o in ('-n', '--nodaemon'):
                daemon = False
        if self.lockfile.is_locked():
            self.e(_('Another instance is running. Aborting'))
        self.default_options()
        self.mod_sys = Module(self.opts)
        self.mod_sys.execute_hook('on_start', {})
        self.packagedir = self.opts.get('default', 'packagedir')
        if daemon:
            try:
                with open(self.opts.get('default', 'logfile'), 'a') as fd:
                    with DaemonContext(pidfile=self.lockfile,
                                       stdout=fd, stderr=fd):
                        self.launcher()
            except ImportError:
                self.w(_('Unable to enter daemon mode'))
                self.lockfile.acquire()
                signal(SIGINT, self.quit)
                self.launcher()
        else:
            self.lockfile.acquire()
            signal(SIGINT, self.quit)
            self.launcher()

    def default_options(self):
        defaultoptions = ('builder', 'packagedir', 'configdir', 'maxbuilds',
                          'pbuilderhooks', 'inotify', 'sleep', 'logfile')
        if not self.conffile:
            self.e(_('Configuration file has not been specified'))
        if not os.path.exists(self.conffile):
            self.err(_('Configuration file %s does not exist') % self.conffile)
        self.opts.read(self.conffile)
        for opt in defaultoptions:
            if not self.opts.has_option('default', opt) or not \
                   self.opts.get('default', opt):
                self.e(_('Set "%(opt)s" in %(conffile)s') %
                       {'opt': opt, 'conffile': self.conffile})

    def launcher(self):
        self.pool = ThreadPool(self.opts.getint('default', 'maxbuilds'))
        self.commandpool = ThreadPool(1)
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
                if (event.name.endswith('source.changes') or
                  event.name.endswith('commands')):
                    self.parent.queue_files([event.name])

        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, PE(self))
        wm.add_watch(self.packagedir, pyinotify.IN_CLOSE_WRITE)
        notifier.loop()

    def launcher_timer(self):
        while True:
            sleep(self.opts.getint('default', 'sleep'))
            self.queue_files()

    def queue_files(self, filelist=None):
        if not filelist:
            try:
                filelist = os.listdir(self.packagedir)
            except OSError:
                self.e(_('Unable to access %s directory') % self.packagedir)
        for filename in filelist:
            if filename.endswith('source.changes'):
                b = FullBuild(self.opts, self.log, package=filename)
                self.pool.add_task(b.run, filename)
            elif filename.endswith('.commands'):
                c = Command(self.opts, self.log, self.pool, filename)
                self.commandpool.add_task(c.process_command, filename)

    def quit(self, signum, frame):
        self.w(_('Waiting for threads to finish, it could take a while...'))
        self.commandpool.wait_completion()
        self.pool.wait_completion()
        self.mod_sys.execute_hook('on_quit', {})
        self.lockfile.release()
        exit()


class Output:

    def w(self, msg):
        stderr.write('%s: %s\n' % (datetime.now().ctime(), msg))

    def e(self, msg):
        self.w(msg)
        exit()

    def t(self, msg):
        self.w(msg)
        raise RuntimeError
