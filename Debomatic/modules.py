# Deb-o-Matic
#
# Copyright (C) 2008-2009 David Futcher
# Copyright (C) 2012-2015 Luca Falavigna
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

from Debomatic import dom
from .process import ModulePool


class ModuleArgs():

    def __init__(self):
        self.opts = dom.opts
        self.action = None
        self.architecture = None
        self.directory = None
        self.distribution = None
        self.dists = None
        self.dsc = None
        self.files = None
        self.package = None
        self.success = False
        self.uploader = None
        self.xarchitecture = None


class Module():

    def __init__(self):
        self.args = ModuleArgs()
        self._use_modules = False
        if dom.opts.has_option('modules', 'modules'):
            if dom.opts.getboolean('modules', 'modules'):
                self._use_modules = True
        if dom.opts.has_option('modules', 'path'):
            mod_path = dom.opts.get('modules', 'path')
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
            missing_after = set()
            for dep in self._instances[module]._depends:
                if dep in self._instances:
                    if self._instances[dep]._disabled:
                        missing.add(dep)
                else:
                    missing.add(dep)
            for dep in self._instances[module]._after:
                if dep in self._instances:
                    if self._instances[dep]._disabled:
                        missing_after.add(dep)
                else:
                    missing_after.add(dep)
            if missing:
                self._instances[module]._disabled = True
                debug(_('%(mod)s module disabled, needs %(missing)s') %
                      {'mod': module, 'missing': ', '.join(missing)})
            if missing_after:
                for dep in missing_after:
                    self._instances[module]._after.remove(dep)

    def _launcher(self, hook):
        func, args, module, hookname, dependencies = hook
        debug(_('Executing hook %(hook)s from module %(mod)s') %
              {'hook': hookname, 'mod': module})
        func(args)

    def _set_blacklisted(self):
        blist = set()
        if dom.opts.has_option('modules', 'blacklist'):
            _blacklist = dom.opts.get('modules', 'blacklist')
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
            try:
                if getattr(self._instances[module], 'first'):
                    deps = (self._instances[module]._depends.union(
                            self._instances[module]._after))
                    if deps:
                        self._instances[module]._disabled = True
                        debug(_('Cannot execute %(mod)s as %(order)s module, '
                                'dependencies found: %(deps)s')
                              % {'mod': module, 'order': 'first',
                                 'deps': ', '.join(deps)})
                    else:
                        for instance in self._instances:
                            self._instances[instance]._after.add(module)
            except AttributeError:
                pass
            try:
                if getattr(self._instances[module], 'last'):
                    deps = [m for m in self._instances
                            if module in self._instances[m]._after or
                            module in self._instances[m]._depends]
                    if deps:
                        self._instances[module]._disabled = True
                        debug(_('Cannot execute %(mod)s as %(order)s module, '
                                'dependencies found: %(deps)s')
                              % {'mod': module, 'order': 'last',
                                 'deps': ', '.join(deps)})
                    else:
                        for instance in self._instances:
                            self._instances[module]._after.add(instance)
            except AttributeError:
                pass
            if module in self._instances[module]._depends:
                self._instances[module]._depend.remove(module)
            if module in self._instances[module]._after:
                self._instances[module]._after.remove(module)

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

    def execute_hook(self, hook):
        hooks = []
        if self._use_modules:
            for module in self._sort_modules():
                if self._instances[module]._disabled:
                    continue
                dependencies = set()
                instance = self._instances[module]
                for dep in instance._depends.union(instance._after):
                    if dep in self._instances:
                        if (dep in instance._after and
                                self._instances[dep]._disabled):
                            continue
                        try:
                            if getattr(self._instances[dep], hook):
                                dependencies.add(dep)
                        except AttributeError:
                            continue
                try:
                    hooks.append((getattr(instance, hook),
                                 self.args, module, hook, dependencies))
                except AttributeError:
                    pass
            if dom.opts.has_option('modules', 'threads'):
                workers = dom.opts.getint('modules', 'threads')
            else:
                workers = 1
            debug(_('%s hooks launched') % hook)
            modulepool = ModulePool(workers)
            for hk in hooks:
                modulepool.schedule(self._launcher, hk)
            modulepool.shutdown()
            debug(_('%s hooks finished') % hook)
