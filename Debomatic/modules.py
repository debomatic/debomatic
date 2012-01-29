# Deb-o-Matic
#
# Copyright (C) 2008-2009 David Futcher
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

    # Set up the modules system
    def __init__(self, opts):
        self.opts = opts
        # Default to having modules enabled
        self.use_modules = True
        self.modules_list = []

        # Check if the modules system is turned on
        if not self.opts.has_option('modules', 'modules'):
            self.use_modules = False
        elif self.opts.get('modules', 'modules') == "0":
            self.use_modules = False
        # Retrieve the path of the blacklist file
        if self.opts.has_option('modules', 'blacklist'):
            self.blacklist = self.opts.get('modules', 'blacklist')
        else:
            self.blacklist = None

        # Add the modules directory to the python path
        if self.opts.has_option('modules', 'modulespath'):
            self.mod_path = self.opts.get('modules', 'modulespath')
            path.append(self.mod_path)
        else:
            self.mod_path = ''

        # Get a list of modules and remove any extra cruft that gets in
        try:
            self.modules_list = os.listdir(self.mod_path)
        except OSError:
            self.use_modules = False

        # Check the user isnt on crack and have actually specified
        # a directory with modules in it
        if len(self.modules_list) == 0:
            self.use_modules = False

        if self.use_modules:
            # Now load the module instances into a dict
            self.instances = {}
            for module in self.modules_list:
                module_split = module.split(".")[:-1]
                module = ""
                for i in module_split:
                    module += i
                try:
                    exec 'from %s import DebomaticModule_%s' % \
                         (module, module)
                    exec 'self.instances["%s"] = DebomaticModule_%s()' % \
                         (module, module)
                except NameError:
                    pass

    # Executes a hook (and all the plugin functions that implement it)
    def execute_hook(self, hook, args):
        if self.use_modules:
            blacklisted_mods = []
            if self.blacklist:
                with open(self.blacklist, 'r') as fd:
                    data = fd.read()
                blacklisted_mods = data.split()
            for module in set(self.instances).difference(blacklisted_mods):
                try:
                    exec 'self.instances["%s"].%s(args)' % (module, hook)
                except AttributeError:
                    pass
