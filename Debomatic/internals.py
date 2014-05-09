# Deb-o-Matic
#
# Copyright (C) 2011-2014 Luca Falavigna
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
from atexit import register as on_exit
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
from hashlib import sha256
from logging import basicConfig as log, debug, error, getLogger, INFO
from signal import SIGTERM
from sys import stdin, stdout, stderr
from threading import Thread
from time import sleep
from traceback import print_exc
from Queue import Queue


class Daemon:
    def __init__(self, pidfile, logfile):
        self.fd = None
        lock_sha = sha256()
        lock_sha.update(pidfile)
        self.pidfile = '/var/run/debomatic-%s.pid' % lock_sha.hexdigest()
        self.logfile = logfile

    def _daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                exit()
        except OSError as e:
            error(_('Error entering daemon mode: %s') % e.strerror)
            exit()
        os.chdir('/')
        os.setsid()
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                exit()
        except OSError as e:
            error(_('Error entering daemon mode: %s') % e.strerror)
            exit()
        stdout.flush()
        stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+', 0)
        os.dup2(si.fileno(), stdin.fileno())
        os.dup2(so.fileno(), stdout.fileno())
        os.dup2(se.fileno(), stderr.fileno())
        on_exit(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as fd:
            fd.write('%s\n' % pid)
        old_log = getLogger()
        if old_log.handlers:
            for handler in old_log.handlers:
                old_log.removeHandler(handler)
        log(filename=self.logfile,
            format='%(asctime)s %(levelname)-8s %(message)s', level=INFO)

    def _delpid(self):
        os.remove(self.pidfile)

    def _getpid(self):
        try:
            with open(self.pidfile, 'r') as fd:
                self.pid = int(pf.read().strip())
        except (IOError, ValueError):
            self.pid = None

    def start(self):
        self._getpid()
        if self.pid:
            error('pidfile %s already exist. Daemon already running?' %
                   self.pidfile)
            exit()
        self._daemonize()
        self.run()

    def stop(self):
        self._getpid()
        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?'
            error('pidfile %s does not exist. Daemon not running?' %
                   self.pidfile)
            return
        self.quit()
        try:
            while True:
                os.kill(pid, SIGTERM)
                sleep(0.5)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                error(err)
                exit()

    def run(self):
        pass

    def quit(self):
        pass


class Singleton:

    def __init__(self, lockfile):
        self.fd = None
        lock_sha = sha256()
        lock_sha.update(lockfile)
        self.lockfile = '/var/run/debomatic-%s.lock' % lock_sha.hexdigest()
        debug(_('Lockfile is %s') % self.lockfile)

    def lock(self, wait=False):
        fd = None
        try:
            fd = open(self.lockfile, 'w')
            flags = LOCK_EX | LOCK_NB if wait else LOCK_EX
            flock(fd, flags)
            self.fd = fd
            return True
        except (OSError, IOError):
            if fd:
                fd.close()
            return False

    def unlock(self):
        if self.fd:
            flock(self.fd, LOCK_UN)
            self.fd.close()
            self.fd = None
        if os.path.isfile(self.lockfile):
            os.unlink(self.lockfile)


class Job(Thread):

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs, jobs = self.tasks.get()
            try:
                func()
            except (RuntimeError, SystemExit):
                pass
            except:
                print_exc()
            try:
                jobs.remove(args)
            except KeyError:
                pass
            self.tasks.task_done()


class ThreadPool:

    def __init__(self, num_threads=1):
        self.jobs = set()
        self.tasks = Queue(num_threads)
        for i in range(num_threads):
            Job(self.tasks)

    def add_task(self, func, *args, **kargs):
        if not args in self.jobs:
            debug(_('Scheduling %(func)s with parameter %(parm)s') %
                  {'func': func.func_name, 'parm': args[0]})
            self.jobs.add(args)
            self.tasks.put((func, args, kargs, self.jobs))
            debug(_('Queue size: %d' % self.tasks.qsize()))
            for queued in self.tasks.queue:
                debug(_('   -> function %(func)s with parameter %(parm)s') %
                             {'func': queued[0].func_name,
                              'parm': queued[1][0]})
            return True
        return False

    def wait_completion(self):
        self.tasks.join()
