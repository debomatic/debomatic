class DebomaticModule_ExampleModule:

    #This code runs just before a package is built
    def pre_build(self, args):
        pass

    #This code runs just after a package is built
    def post_build(self, args):
        pass

    #This code is run on Debomatic startup
    def on_start(self, args):
        pass

### HOOK ARGUMENTS
# Some hooks are passed arguments, in the form of a python dictionary, to
# help make the modules system more poweful:
#
## pre_build(), post_build():
#
# 'directory':    The distributions working directory. Binary build results
#                 are held in $directory/pool
# 'package':      The name and version of the package being built in the form
#                 of "packagename-version.version.etc"
# 'cfg':          Configfile
# 'distribution': The name of the target distribution (Intrepid, Unstable, etc.
# 'dsc':          Dsc filename
