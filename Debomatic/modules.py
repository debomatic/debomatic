# Deb-o-Matic
#
# Copyright (C) 2008 David Futcher
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

import sys
import os
from Debomatic import Options

class Module:

    # Set up the modules system
    def __init__(self):
        # Default to having modules enabled
        self.use_modules = True

        # Check if the modules system is turned on
        if not Options.has_option('modules', 'modules'):
            self.use_modules = False
        elif Options.get('modules', 'modules') == "0":
            self.use_modules = False

        # Add the modules directory to the python path
        self.mod_path = Options.get('modules', 'modulespath')
        sys.path.append(self.mod_path)

        # Get a list of modules and remove any extra cruft that gets in the list
        self.modules_list = os.listdir(self.mod_path)

        # Check the user isnt on crack and have actually specified a directory with modules in it
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
                    exec "from %s import DebomaticModule_%s" % (module, module)
                    exec "self.instances['%s'] = DebomaticModule_%s()" % (module, module)
                except:
                    pass    

    # Executes a hook (and all the plugin functions that implement it)
    def execute_hook(self, hook, args):
        if self.use_modules:
            for module in self.instances:
                try:
                    exec "self.instances['%s'].%s(args)" % (module, hook)
                except AttributeError:
                    pass

