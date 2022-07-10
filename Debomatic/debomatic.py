# Deb-o-Matic
#
# Copyright (C) 2007-2022 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option), any later version.
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
from argparse import ArgumentParser
from configparser import ConfigParser
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
from logging import basicConfig as log, debug, error, getLogger, warning
from logging import ERROR, WARNING, INFO, DEBUG
from time import sleep

from Debomatic import dom
from .build import Build
from .commands import Command
from .configuration import Parser
from .exceptions import DebomaticConffileError, DebomaticError
from .modules import Module
from .process import Process, ThreadPool, Timer


class Debomatic(Parser, Process):

    def __init__(self):
        self.daemonize = True
        self.oneshot = False
        self.setlog('%(levelname)s: %(message)s')
        self.conffile = None
        dom.opts = ConfigParser()
        dom.dists = ConfigParser()
        parser = ArgumentParser()
        parser.add_argument('-c', '--configfile', metavar='file', type=str,
                            nargs=1, help='configuration file for Deb-o-Matic')
        parser.add_argument('-i', '--interactive', action='store_true',
                            help='launch Deb-o-Matic in interactive mode')
        parser.add_argument('-o', '--oneshot', metavar='file', type=str,
                            nargs=1, help='launch Deb-o-Matic for one build')
        parser.add_argument('-q', '--quit', action='store_true',
                            help='terminate Deb-o-Matic processes')
        args = parser.parse_args()
        if os.getuid():
            error(_('You must run Deb-o-Matic as root'))
            exit(1)
        if args.configfile:
            self.conffile = args.configfile[0]
        if args.interactive:
            self.daemonize = False
        if args.oneshot:
            self.oneshot = args.oneshot[0]
        try:
            self.parse_configfiles()
        except DebomaticConffileError:
            exit(1)
        self.incoming = dom.opts.get('debomatic', 'incoming')
        if not os.path.isdir(self.incoming):
            error(_('Unable to access %s directory') % self.incoming)
            exit(1)
        dom.pool = ThreadPool(dom.opts.getint('debomatic', 'threads'))
        dom.periodic_event = Timer(dom.opts.getint('debomatic', 'interval'),
                                   self.periodic_event)
        dom.buildqueue = []
        dom.chroots = {}
        self.logfile = dom.opts.get('debomatic', 'logfile')
        if args.quit:
            self.shutdown()
            exit()
        self.setlog('%(levelname)s: %(message)s',
                    dom.opts.get('debomatic', 'loglevel'))
        self.mod_sys = Module()
        self.mod_sys.execute_hook('on_start')
        try:
            self.startup()
        except DebomaticError:
            error(_('Another instance is running, aborting'))
            exit(1)

    def launcher(self):
        if self.oneshot:
            self.queue_files([self.oneshot])
        else:
            self.queue_files()
            if dom.opts.getboolean('debomatic', 'inotify'):
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
        wm.add_watch(self.incoming, pyinotify.IN_CLOSE_WRITE)
        debug(_('Inotify loop started'))
        notifier.loop()

    def launcher_timer(self):
        debug(_('Timer loop started'))
        while True:
            sleep(dom.opts.getint('debomatic', 'sleep'))
            self.queue_files()

    def queue_files(self, filelist=None):
        if filelist:
            filelist = [os.path.join(self.incoming, os.path.basename(f))
                        for f in filelist]
            for f in filelist:
                if not os.path.isfile(f):
                    filelist.remove(f)
        else:
            try:
                filelist = os.listdir(self.incoming)
            except OSError:
                error(_('Unable to access %s directory') % self.incoming)
                exit(1)
        for filename in filelist:
            if filename.endswith('.changes'):
                with open(os.path.join(self.incoming, filename)) as fd:
                    try:
                        flock(fd, LOCK_EX | LOCK_NB)
                        flock(fd, LOCK_UN)
                    except IOError:
                        pass
                    else:
                        b = Build(changesfile=filename)
                        dom.pool.schedule(b.run)
                        debug(_('Thread for %s scheduled') % filename)
            elif filename.endswith('.commands'):
                Command(filename)
        if self.oneshot:
            self.shutdown()

    def setlog(self, fmt, level='info'):
        loglevels = {'error': ERROR,
                     'warning': WARNING,
                     'info': INFO,
                     'debug': DEBUG}
        level = level.lower()
        if level not in loglevels:
            warning(_('Log level not valid, defaulting to "info"'))
            level = 'info'
        self.loglevel = loglevels[level]
        old_log = getLogger()
        if old_log.handlers:
            for handler in old_log.handlers:
                old_log.removeHandler(handler)
        log(level=self.loglevel, format=fmt)

    def periodic_event(self):
        self.mod_sys.args.opts = dom.opts
        self.mod_sys.args.directory = self.incoming
        self.mod_sys.execute_hook('periodic')
