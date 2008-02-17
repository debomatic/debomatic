# Deb-o-Matic
#
# Copyright (C) 2007-2008 Luca Falavigna
#
# Author: Luca Falavigna <dktrkranz@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; only version 2 of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

import threading
from time import sleep
from Debomatic import globals
from Debomatic import build

try:
    import os
    from re import findall
    from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent

    class PE(ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event):
            if findall('source.changes$', event.name):
                threading.Thread(None, build.build_process).start()

    def launcher_inotify():
        if globals.Options.getint('default', 'inotify'):
            wm = WatchManager()
            notifier = Notifier(wm, PE())
            wm.add_watch(globals.Options.get('default', 'packagedir'), EventsCodes.IN_CLOSE_WRITE, rec=True)
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
        sleep(globals.Options.getint('default', 'sleep'))

def launcher():
    threading.Thread(None, launcher_inotify).start()
    threading.Thread(None, launcher_timer).start()

