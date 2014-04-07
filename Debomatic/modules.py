# Deb-o-Matic
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2012-2013 Luca Falavigna
#
# Author: David Futcher <bobbo@ubuntu.com>
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
from sys import path


class Module():

    def __init__(self, opts):
        (self.log, self.opts, self.rtopts, self.conffile) = opts
        self.use_modules = True
        self.modules_list = set()
        if not self.opts.has_option('modules', 'modules'):
            self.use_modules = False
        elif self.opts.get('modules', 'modules') == "0":
            self.use_modules = False
        if self.opts.has_option('modules', 'modulespath'):
            self.mod_path = self.opts.get('modules', 'modulespath')
            path.append(self.mod_path)
        else:
            self.mod_path = ''
        try:
            self.modules_list = set(os.listdir(self.mod_path))
        except OSError:
            self.use_modules = False
        if not self.modules_list:
            self.use_modules = False
        if self.use_modules:
            self.instances = {}
            for module in self.modules_list:
                if module.endswith('.pyc'):
                    continue
                module_split = module.split(".")[:-1]
                module = ""
                for i in module_split:
                    module += i
                try:
                    exec('from %s import DebomaticModule_%s' %
                         (module, module))
                    exec('self.instances["%s"] = DebomaticModule_%s()' %
                         (module, module))
                    self.log.w(_('Module %s loaded' % module), 3)
                except NameError:
                    pass

    def execute_hook(self, hook, args):
        if self.use_modules:
            self.rtopts.read(self.conffile)
            if self.rtopts.has_option('runtime', 'modulesblacklist'):
                blist_mods = self.rtopts.get('runtime', 'modulesblacklist')
                blist_mods = blist_mods.split()
            else:
                blist_mods = []
            modules = [i for i in self.instances.keys()
                       if i not in blist_mods]
            modules.sort()
            for module in modules:
                try:
                    self.log.w(_('Executing hook %s from module %s' %
                                 (hook, module)), 3)
                    exec 'self.instances["%s"].%s(args)' % (module, hook)
                except AttributeError:
                    pass
