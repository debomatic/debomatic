from logging import debug, error, info
from time import sleep
from ast import literal_eval

class DebomaticModule_Retry:
    def __init__(self):
        pass

    def post_build(self, args):
        if args.success:
            return

        map = dict()
        if args.opts.has_section('retry'):
            map = literal_eval(args.opts.get('retry', 'dists'))

        failed_dist = args.distribution
        if not failed_dist in map:
            debug('not requeueing %s failure (%s not in retry.dists)' % (args.package, failed_dist))
            return

        retry_dist = map[failed_dist]
        info('requeuing %s in %s' % (args.package, retry_dist))

        incoming = args.opts.get('debomatic', 'incoming')
        commands_file = 'retry-%s-%s-%s.commands' % (failed_dist, retry_dist, args.package)

        with open('%s/%s' % (incoming, commands_file), 'w') as fd:
            command = 'rebuild %s %s' % (args.package, retry_dist)
            fd.write(command + '\n')

        # work around a race condition with sbuild
        sleep(10)
