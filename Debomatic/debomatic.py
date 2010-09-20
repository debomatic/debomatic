# Deb-o-Matic
#
# Copyright (C) 2007-2010 Luca Falavigna
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
import sys
import threading
from fcntl import lockf, LOCK_EX, LOCK_NB
from getopt import getopt, GetoptError
from signal import pause
from time import sleep
from Debomatic import build
from Debomatic import commands
from Debomatic import Options
from Debomatic import modules
from Debomatic import running

def main():
    conffile = None
    daemon = True
    if os.getuid():
        print _('You must run deb-o-matic as root')
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
            print _('Unable to enter daemon mode')
            sys.exit(-1)
        os.setsid()
        os.chdir('/')
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            print _('Unable to enter daemon mode')
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
        print _('Another instance is running. Aborting')
        sys.exit(-1)
    mod_sys = modules.Module()
    mod_sys.execute_hook("on_start", {})
    launcher()

def parse_default_options(conffile):
    defaultoptions = ('builder', 'packagedir', 'configdir', 'maxbuilds', 'inotify', 'sleep', 'logfile')
    if not conffile:
        print _('Please specify a configuration file')
        sys.exit(-1)
    if not os.path.exists(conffile):
        print _('Configuration file %s does not exist') % conffile
        sys.exit(-1)
    Options.read(conffile)
    for opt in defaultoptions:
        if not Options.has_option('default', opt) or not Options.get('default', opt):
            print _('Please set "%(opt)s" in %(conffile)s') % {'opt':opt, 'conffile':conffile}
            sys.exit(-1)

try:
    import os
    import pyinotify
    from re import findall

    class PE(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event):
            if findall('source.changes$', event.name):
                threading.Thread(None, build.build_process).start()
            elif findall('commands$', event.name):
                threading.Thread(None, commands.process_commands).start()

    def launcher_inotify():
        if Options.getint('default', 'inotify'):
            wm = pyinotify.WatchManager()
            notifier = pyinotify.Notifier(wm, PE())
            wm.add_watch(Options.get('default', 'packagedir'), pyinotify.IN_CLOSE_WRITE, rec=True)
            notifier.loop(callback=exit_routine)
except:
    def launcher_inotify():
        pass

def launcher_timer():
    while exit_routine():
        threading.Thread(None, commands.process_commands).start()
        threading.Thread(None, build.build_process).start()
        sleep(Options.getint('default', 'sleep'))

def launcher():
    threading.Thread(None, launcher_inotify).start()
    threading.Thread(None, launcher_timer).start()
    try:
        pause()
    except KeyboardInterrupt:
        print _('\nWaiting for threads to finish, it could take a while...')
        exit_routine(exiting=True)

def exit_routine(self=None, exiting=False):
    global running
    if exiting:
        running = False
        return
    if not running:
        sys.exit(0)
    return running
