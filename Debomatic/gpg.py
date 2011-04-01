# Deb-o-Matic
#
# Copyright (C) 2007-2011 Luca Falavigna
# Copyright (C) 2010 Alessio Treglia
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
from re import findall, DOTALL
from subprocess import Popen, PIPE

from Debomatic import acceptedqueue, Options


def verify_signature(pkg_or_cmd):
    gpgresult = Popen(['gpg', '--no-default-keyring', '--keyring',
                      Options.get('gpg', 'keyring'), '--verify', pkg_or_cmd],
                      stderr=PIPE).communicate()[1]
    ID = findall('Good signature from "(.*) <(.*)>"', gpgresult)
    if not ID:
        return None
    return ID[0]


def check_changes_signature(package):
    if Options.getint('gpg', 'gpg'):
        if not Options.has_option('gpg', 'keyring') or not \
               os.path.exists(Options.get('gpg', 'keyring')):
            raise RuntimeError(_('Keyring not found'))
        if not package in acceptedqueue:
            signature = verify_signature(package)
            if not signature:
                raise RuntimeError(_('No valid signatures found'))
            with open(package, 'r') as fd:
                data = fd.read()
            with open(package, 'w') as fd:
                try:
                    fd.write(findall('\n\n(.*?)\n\n?-', data, DOTALL)[0])
                except IndexError:
                    raise RuntimeError(_('No valid signatures found'))
            if not package in acceptedqueue:
                acceptedqueue.append(package)
            return signature


def check_commands_signature(commands):
    if Options.getint('gpg', 'gpg'):
        if not Options.has_option('gpg', 'keyring') or not \
               os.path.exists(Options.get('gpg', 'keyring')):
            raise RuntimeError(_('Keyring not found'))
        signature = verify_signature(commands)
        if not signature:
            raise RuntimeError(_('No valid signatures found'))
        with open(commands, 'r') as fd:
            data = fd.read()
        with open(commands, 'w') as fd:
            try:
                fd.write(findall('\n\n(.*?)\n\n?-', data, DOTALL)[0])
            except IndexError:
                raise RuntimeError(_('No valid signatures found'))
