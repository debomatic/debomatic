# Deb-o-Matic
#
# Copyright (C) 2011-2013 Luca Falavigna
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

from Queue import Queue
from threading import Thread
from traceback import print_exc


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

    def __init__(self, num_threads):
        self.jobs = set()
        self.tasks = Queue(num_threads)
        for i in range(num_threads):
            Job(self.tasks)

    def add_task(self, func, *args, **kargs):
        if not args in self.jobs:
            self.jobs.add(args)
            self.tasks.put((func, args, kargs, self.jobs))
            return True
        return False

    def wait_completion(self):
        self.tasks.join()
