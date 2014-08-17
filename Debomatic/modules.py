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
from re import findall
from sys import path
from toposort import toposort_flatten as toposort

from .process import ModulePool


class Module():

    def __init__(self, opts):
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
            for module in modules:
                try:
                    _class = 'DebomaticModule_%s' % module
                    _mod = __import__(module)
                    self._instances[module] = getattr(_mod, _class)()
                    self._instances[module]._modulename = module
                    self._instances[module]._disabled = False
                    self._instances[module]._depends = set()
                    self._instances[module]._after = set()
                    debug(_('Module %s loaded') % module)
                except (NameError, SyntaxError):
                    pass
            self._set_relationships()
            self._set_blacklisted()
            self._disable_modules()
            debug(_('Modules will be executed in this order: %s') %
                  ', '.join([m for m in self._sort_modules()
                               if not self._instances[m]._disabled]))

    def _disable_modules(self):
        for module in self._sort_modules():
            missing = set()
            for dep in self._instances[module]._depends:
                if dep in self._instances:
                    if self._instances[dep]._disabled:
                        missing.add(dep)
                else:
                    missing.add(dep)
            if missing:
                self._instances[module]._disabled = True
                debug(_('%s module disabled, needs %s') %
                      (module, ', '.join(missing)))

    def _launcher(self, hook):
        func, args, module, hookname, dependencies = hook
        debug(_('Executing hook %(hook)s from module %(mod)s') %
              {'hook': hookname, 'mod': module})
        func(args)

    def _set_blacklisted(self):
        blist = set()
        if self._rtopts.has_option('runtime', 'modulesblacklist'):
            _blacklist = self._rtopts.get('runtime', 'modulesblacklist')
            blist = set(_blacklist.split())
        for module in self._instances:
            if module in blist:
                self._instances[module]._disabled = True
                debug(_('Module %s is blacklisted') % module)

    def _set_relationships(self):
        for module in self._instances:
            try:
                deps = getattr(self._instances[module], 'dependencies')
                if deps:
                    for dep in deps:
                        self._instances[module]._depends.add(dep)
            except AttributeError:
                pass
            try:
                afters = getattr(self._instances[module], 'after')
                if afters:
                    for after in afters:
                        self._instances[module]._after.add(after)
            except AttributeError:
                pass
            try:
                befores = getattr(self._instances[module], 'before')
                if befores:
                    for before in befores:
                        if before in self._instances:
                            self._instances[before]._after.add(module)
            except AttributeError:
                pass

    def _sort_modules(self):
        modules = {}
        for instance in self._instances:
            if not self._instances[instance]._disabled:
                _deps = self._instances[instance]._depends
                _afters = self._instances[instance]._after
                modules[instance] = _deps.union(_afters)
        try:
            return [m for m in toposort(modules) if m in self._instances]
        except ValueError as e:
            circular = findall('.*?\(\'?(\S+?)\'?,', e.args[0])
            for instance in circular:
                self._instances[instance]._disabled = True
            debug(_('Circular dependencies found, disabled modules: %s')
                  % ', '.join(circular))
            return self._sort_modules()

    def execute_hook(self, hook, args):
        hooks = []
        if self._use_modules:
            for module in self._sort_modules():
                if self._instances[module]._disabled:
                    continue
                dependencies = set()
                instance = self._instances[module]
                for dep in instance._depends.union(instance._after):
                    if dep in self._instances:
                        dependencies.add(dep)
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
