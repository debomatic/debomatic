# Deb-o-Matic
#
# Copyright (C) 2015-2025 Luca Falavigna
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
from ast import literal_eval
from configparser import NoOptionError
from logging import error

from Debomatic import dom
from .exceptions import DebomaticConffileError


core = {'debomatic':
        {'incoming': str, 'architecture': str, 'threads': int, 'inotify': bool,
         'sleep': int, 'interval': int, 'logfile': str, 'loglevel': str},
        'distributions': {'list': str, 'blacklist': str, 'mapper': dict},
        'chroots': {'commands': str},
        'gpg': {'gpg': bool, 'keyring': str},
        'modules': {'modules': bool, 'path': str,
                    'threads': int, 'blacklist': str}}
optional = {'crossbuild': {'crossbuild': bool, 'hostarchitecture': str},
            'dpr': {'dpr': bool, 'prefix': str, 'repository': str}}
modules = {'autopkgtest': {'options': str},
           'blhc': {'options': str},
           'buildcleaner': {'testbuild': bool},
           'lintian': {'options': str},
           'mailer': {'sender': str, 'server': str, 'port': int, 'tls': bool,
                      'authrequired': bool, 'user': str, 'passwd': str,
                      'success': str, 'failure': str, 'lintian': bool},
           'piuparts': {'options': str},
           'repository': {'gpgkey': str, 'keyring': str}}
dists = {'suite': str, 'mirror': str, 'components': str,
         '_extramirrors': str, '_extrapackages': str}


class Parser:

    def __init__(self):
        pass

    def _validate(self, option, section, configtype, element, conffile):
        if not element.has_option(section, option):
            if not option.startswith('_'):
                error(_('Set "%(option)s" in section "%(section)s" '
                        'in %(conffile)s') % {'option': option.strip('_'),
                                              'section': section,
                                              'conffile': conffile})
                raise DebomaticConffileError
        fubar = False
        try:
            if configtype == int:
                _option = element.getint(section, option)
            elif configtype == bool:
                _option = element.getboolean(section, option)
            elif configtype == dict:
                _option = literal_eval(element.get(section, option))
            else:
                _option = element.get(section, option)
            assert isinstance(_option, configtype)
        except NoOptionError:
            if not option.startswith('_'):
                fubar = True
        except (AssertionError, ValueError):
            fubar = True
        finally:
            if fubar:
                error(_('Option "%(option)s" in section "%(section)s" '
                        'must be %(type)s' % {'option': option,
                                              'section': section,
                                              'type': configtype.__name__}))
                raise DebomaticConffileError

    def parse_configfiles(self):
        if not self.conffile:
            error(_('Configuration file has not been specified'))
            raise DebomaticConffileError
        if not os.path.isfile(self.conffile):
            error(_('Configuration file %s does not exist') % self.conffile)
            raise DebomaticConffileError
        dom.opts.read(self.conffile)
        for section in core:
            if not dom.opts.has_section(section):
                error(_('Section "%(section)s" missing in %(conffile)s') %
                      {'section': section, 'conffile': self.conffile})
                raise DebomaticConffileError
            for option in core[section]:
                self._validate(option, section, core[section][option],
                               dom.opts, self.conffile)
        for section in optional:
            if dom.opts.has_section(section):
                for option in optional[section]:
                    self._validate(option, section, optional[section][option],
                                   dom.opts, self.conffile)
        for section in modules:
            if dom.opts.has_section(section):
                for option in modules[section]:
                    self._validate(option, section, modules[section][option],
                                   dom.opts, self.conffile)
        distfile = dom.opts.get('distributions', 'list')
        if not os.path.isfile(distfile):
            error(_('Distribution file %s does not exist') % distfile)
            raise DebomaticConffileError
        dom.dists.read(distfile)
        for dist in dom.dists.sections():
            for option in dists:
                self._validate(option, dist, dists[option],
                               dom.dists, distfile)
