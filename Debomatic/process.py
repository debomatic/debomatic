# Deb-o-Matic
#
# Copyright (C) 2011-2024 Luca Falavigna
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
from concurrent.futures import as_completed, ThreadPoolExecutor
from atexit import register as on_exit
from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
from hashlib import sha256
from logging import basicConfig as log, error, getLogger, info
from signal import signal, SIGINT, SIGTERM
from sys import stdin, stdout, stderr
from threading import Timer as _Timer
from time import sleep

from Debomatic import dom
from .exceptions import DebomaticError


class Process:

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
        stdout.flush()
        stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')
        os.dup2(si.fileno(), stdin.fileno())
        os.dup2(so.fileno(), stdout.fileno())
        os.dup2(se.fileno(), stderr.fileno())
        on_exit(self._quit)
        old_log = getLogger()
        if old_log.handlers:
            for handler in old_log.handlers:
                old_log.removeHandler(handler)
        log(filename=self.logfile, level=self.loglevel,
            format='%(asctime)s %(levelname)-8s %(message)s')
        self._set_pid()

    def _get_pid(self):
        self.pidfile = (
            f'/tmp/debomatic-{self._sha256(self.incoming)}')
        try:
            with open(self.pidfile, 'r') as fd:
                self.pid = int(fd.read().strip())
        except (IOError, ValueError):
            self.pid = None

    def _lock(self, wait=False):
        self.fd = None
        self.lockfile = (
            f'/tmp/debomatic-{self._sha256(self.incoming)}.lock')
        try:
            self.fd = open(self.lockfile, 'w')
            flags = LOCK_EX if wait else LOCK_EX | LOCK_NB
            flock(self.fd, flags)
        except (OSError, IOError) as ex:
            if self.fd:
                self.fd.close()
            raise ex

    def _notify_systemd(self):
        try:
            import systemd.daemon
            systemd.daemon.notify('READY=1')
        except (ImportError, SystemError):
            pass

    def _quit(self, signum=None, frame=None):
        info(_('Waiting for threads to complete...'))
        dom.periodic_event.cancel()
        dom.pool.shutdown()
        self.mod_sys.execute_hook('on_quit')
        self._unlock()
        os.unlink(self.pidfile)
        exit()

    def _set_pid(self):
        self.pidfile = (
            f'/tmp/debomatic-{self._sha256(self.incoming)}')
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as fd:
            fd.write('%s\n' % pid)

    def _sha256(self, value):
        lock_sha = sha256()
        lock_sha.update(value.encode('utf-8'))
        return lock_sha.hexdigest()

    def _unlock(self):
        if self.fd:
            flock(self.fd, LOCK_UN)
            self.fd.close()
            self.fd = None
        if os.path.isfile(self.lockfile):
            os.unlink(self.lockfile)

    def shutdown(self):
        self._get_pid()
        if not self.pid:
            return
        info(_('Waiting for threads to complete...'))
        try:
            dom.periodic_event.cancel()
            os.kill(self.pid, SIGTERM)
            self._lock(wait=True)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.unlink(self.pidfile)
            else:
                error(err)

    def startup(self):
        try:
            self._lock()
        except (OSError, IOError):
            error(_('Another instance is running, aborting'))
            raise DebomaticError
        self._set_pid()
        signal(SIGINT, self._quit)
        signal(SIGTERM, self._quit)
        if self.daemonize:
            self._daemonize()
        self._notify_systemd()
        dom.periodic_event.start()
        self.launcher()


class ModulePool:

    def __init__(self, workers=1):
        self._jobs = {}
        self._pool = ThreadPoolExecutor(workers)

    def _launch(self, func, hook, dependencies):
        if dependencies:
            for dependency in dependencies:
                while True:
                    if dependency in self._jobs.keys():
                        self._jobs[dependency].result()
                        break
                    else:
                        sleep(0.1)
        func(hook)

    def schedule(self, func, hook):
        innerfunc, args, module, hookname, dependencies = hook
        job = self._pool.submit(self._launch, func, hook, dependencies)
        self._jobs[module] = job

    def shutdown(self):
        for job in as_completed([self._jobs[j] for j in self._jobs]):
            job.result()
        self._pool.shutdown()


class ThreadPool:

    def __init__(self, workers=1):
        self._jobs = []
        self._pool = ThreadPoolExecutor(workers)

    def _finish(self, job):
        try:
            self._jobs.remove(job)
        except ValueError:
            pass
        try:
            e = job.exception()
            if e:
                raise e
        except Exception as e:
            error(str(e), exc_info=True)

    def schedule(self, func):
        job = self._pool.submit(func)
        job.add_done_callback(self._finish)
        self._jobs.append(job)

    def shutdown(self):
        for job in as_completed(self._jobs):
            job.result()
        self._pool.shutdown()


class Timer(_Timer):

    def run(self):
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
        self.finished.set()
