# Deb-o-Matic
#
# Copyright (C) 2007-2009 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
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
import sys
import threading
from fcntl import lockf, LOCK_EX, LOCK_NB
from getopt import getopt, GetoptError
from time import sleep
from Debomatic import build
from Debomatic import Options
from Debomatic import modules

def main():
    conffile = None
    daemon = True
    if os.getuid():
        print 'You must run deb-o-matic as root'
        sys.exit(-1)
    try:
        opts, args = getopt(sys.argv[1:], 'c:n', ['config=', 'nodaemon'])
    except GetoptError, error:
        print error.msg
        sys.exit(-1)
    for o, a in opts:
        if o in ("-c", "--config"):
            conffile = a
        if o in ('-n', '--nodaemon'):
            daemon = False
    parse_default_options(conffile)

    # If daemon mode is set, detach from the terminal and run in background.
    if daemon:
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            print 'Fork failed'
            sys.exit(-1)
        os.setsid()
        os.chdir('/')
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            print 'Fork failed'
            sys.exit(-1)
        fin = open('/dev/null', 'r')
        fout = open(Options.get('default', 'logfile'), 'a+')
        ferr = open(Options.get('default', 'logfile'), 'a+', 0)
        os.dup2(fin.fileno(), sys.stdin.fileno())
        os.dup2(fout.fileno(), sys.stdout.fileno())
        os.dup2(ferr.fileno(), sys.stderr.fileno())

    fd = os.open('/var/run/debomatic.lock', os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    try:
        lockf(fd, LOCK_EX | LOCK_NB)
    except IOError:
        print 'Another instance is running. Aborting.'
        sys.exit(-1)
    mod_sys = modules.Module()
    mod_sys.execute_hook("on_start", {})
    launcher()

def parse_default_options(conffile):
    defaultoptions = ('packagedir', 'configdir', 'maxbuilds', 'inotify', 'sleep', 'logfile')
    if not conffile:
        print 'Please specify a configuration file'
        sys.exit(-1)
    if not os.path.exists(conffile):
        print 'Configuration file %s does not exist' % conffile
        sys.exit(-1)
    Options.read(conffile)
    for opt in defaultoptions:
        if not Options.has_option('default', opt) or not Options.get('default', opt):
            print 'Please set "%s" in %s' % (opt, conffile)
            sys.exit(-1)

try:
    import os
    from re import findall
    from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent

    class PE(ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event):
            if findall('source.changes$', event.name):
                threading.Thread(None, build.build_process).start()

    def launcher_inotify():
        if Options.getint('default', 'inotify'):
            wm = WatchManager()
            notifier = Notifier(wm, PE())
            wm.add_watch(Options.get('default', 'packagedir'), EventsCodes.IN_CLOSE_WRITE, rec=True)
            while True:
                try:
                    notifier.process_events()
                    if notifier.check_events():
                        notifier.read_events()
                except KeyboardInterrupt:
                    notifier.stop()
                    break
except:
    def launcher_inotify():
        pass

def launcher_timer():
    while 1:
        threading.Thread(None, build.build_process).start()
        sleep(Options.getint('default', 'sleep'))

def launcher():
    threading.Thread(None, launcher_inotify).start()
    threading.Thread(None, launcher_timer).start()

