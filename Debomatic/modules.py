# Deb-o-Matic
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2012-2014 Luca Falavigna
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
from glob import glob
from logging import debug
from sys import path

from .process import ModulePool


class Module():

    def __init__(self, opts):
        blist = []
        (self._opts, self._rtopts, self._conffile) = opts
        self._use_modules = False
        if self._opts.has_option('modules', 'modules'):
            if self._opts.getint('modules', 'modules'):
                self._use_modules = True
        if self._opts.has_option('modules', 'modulespath'):
            mod_path = self._opts.get('modules', 'modulespath')
            path.append(mod_path)
        else:
            self._use_modules = False
        try:
            modules = set([os.path.splitext(os.path.basename(m))[0] for m in
                           glob(os.path.join(mod_path, '*.py'))])
        except OSError:
            self._use_modules = False
        if not modules:
            self._use_modules = False
        if self._use_modules:
            self._instances = {}
            self._rtopts.read(self._conffile)
            if self._rtopts.has_option('runtime', 'modulesblacklist'):
                blist = self._rtopts.get('runtime', 'modulesblacklist').split()
            for module in modules:
                try:
                    _class = 'DebomaticModule_%s' % module
                    _mod = __import__(module)
                    self._instances[module] = getattr(_mod, _class)()
                    self._instances[module]._enabled = True
                    self._instances[module]._depends = set()
                    try:
                        deps = getattr(self._instances[module], 'dependencies')
                        if deps:
                            for dep in deps:
                                self._instances[module]._depends.add(dep)
                    except AttributeError:
                        pass
                    self._instances[module]._enhances = set()
                    self._instances[module]._missing = set()
                    self._instances[module]._modulename = module
                    debug(_('Module %s loaded') % module)
                except (NameError, SyntaxError):
                    pass
            for instance in self._instances:
                instance = self._instances[instance]
                module = instance._modulename
                for dep in instance._depends:
                    if dep in self._instances:
                        self._instances[dep]._enhances.add(module)
                if module in blist:
                    instance._enabled = False
                    debug(_('Module %s is blacklisted') % module)
            for module in self._instances:
                self._check_dependencies(module)

    def _check_dependencies(self, module):
        instance = self._instances[module]
        for dep in self._instances[module]._depends:
            if dep in self._instances:
                if not self._instances[dep]._enabled:
                    instance._enabled = False
                    instance._missing.add(dep)
            else:
                instance._enabled = False
                instance._missing.add(dep)
        if not instance._enabled:
            if instance._missing:
                debug(_('%s module disabled, needs %s') %
                      (instance._modulename, ', '.join(instance._missing)))
            for module in instance._enhances:
                self._check_dependencies(module)

    def _launcher(self, hook):
        func, args, module, hookname, dependencies = hook
        debug(_('Executing hook %(hook)s from module %(mod)s') %
              {'hook': hookname, 'mod': module})
        func(args)

    def execute_hook(self, hook, args):
        hooks = []
        if self._use_modules:
            for instance in [self._instances[m]
                             for m in sorted(self._instances)
                             if self._instances[m]._enabled]:
                module = instance._modulename
                dependencies = instance._depends
                try:
                    hooks.append((getattr(instance, hook),
                                 args, module, hook, dependencies))
                except AttributeError:
                    pass
            if self._opts.has_option('modules', 'maxthreads'):
                workers = self._opts.getint('modules', 'maxthreads')
            else:
                workers = 1
            modulepool = ModulePool(workers)
            for hk in hooks:
                modulepool.schedule(self._launcher, hk)
            modulepool.wait()
