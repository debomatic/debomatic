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
from logging import basicConfig as log, debug, error, getLogger, info, INFO
from signal import signal, SIGINT, SIGTERM
from sys import stdin, stdout, stderr
from threading import Thread
from time import sleep
from traceback import print_exc
from queue import Queue


class Daemon:
    def __init__(self):
        pass

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
        on_exit(self._on_quit)
        old_log = getLogger()
        if old_log.handlers:
            for handler in old_log.handlers:
                old_log.removeHandler(handler)
        log(filename=self.logfile,
            format='%(asctime)s %(levelname)-8s %(message)s', level=INFO)
        self._set_pid()
        self.launcher()

    def _get_pid(self):
        self.pidfile = ('/var/run/debomatic-%s.pid' %
                        self._get_sha256(self.packagedir))
        try:
            with open(self.pidfile, 'r') as fd:
                self.pid = int(fd.read().strip())
        except (IOError, ValueError):
            self.pid = None

    def _set_pid(self):
        self.pidfile = ('/var/run/debomatic-%s.pid' %
                        self._get_sha256(self.packagedir))
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as fd:
            fd.write('%s\n' % pid)

    def _lock(self, wait=False):
        self.fd = None
        self.lockfile = ('/var/run/debomatic-%s.lock' %
                         self._get_sha256(self.packagedir))
        try:
            self.fd = open(self.lockfile, 'w')
            flags = LOCK_EX if wait else LOCK_EX | LOCK_NB
            flock(self.fd, flags)
        except (OSError, IOError) as ex:
            if self.fd:
                self.fd.close()
            raise ex

    def _unlock(self):
        if self.fd:
            flock(self.fd, LOCK_UN)
            self.fd.close()
            self.fd = None
        if os.path.isfile(self.lockfile):
            os.unlink(self.lockfile)

    def _on_quit(self, signum=None, frame=None):
        info(_('Waiting for threads to complete...'))
        self.commandpool.wait_completion()
        self.pool.wait_completion()
        debug(_('Shutdown hooks launched'))
        self.mod_sys.execute_hook('on_quit', {})
        debug(_('Shutdown hooks finished'))
        self._unlock()
        os.unlink(self.pidfile)
        exit()

    def _get_sha256(self, value):
        lock_sha = sha256()
        lock_sha.update(value.encode('utf-8'))
        return lock_sha.hexdigest()

    def startup(self):
        try:
            self._lock()
        except (OSError, IOError):
            error(_('Another instance is running, aborting'))
            raise RuntimeError
        self._set_pid()
        signal(SIGINT, self._on_quit)
        signal(SIGTERM, self._on_quit)
        if self.daemonize:
            self._daemonize()
        else:
            self.launcher()

    def shutdown(self):
        self._get_pid()
        if not self.pid:
            return
        info(_('Waiting for threads to complete...'))
        try:
            os.kill(self.pid, SIGTERM)
            self._lock(wait=True)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.unlink(self.pidfile)
            else:
                error(err)


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
                  {'func': func.__name__, 'parm': args[0]})
            self.jobs.add(args)
            self.tasks.put((func, args, kargs, self.jobs))
            debug(_('Queue size: %d' % self.tasks.qsize()))
            for queued in self.tasks.queue:
                debug(_('   -> function %(func)s with parameter %(parm)s') %
                      {'func': queued[0].__name__, 'parm': queued[1][0]})
            return True
        return False

    def wait_completion(self):
        self.tasks.join()
