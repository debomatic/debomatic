# Deb-o-Matic - Mailer module
#
# Copyright (C) 2010 Alessio Treglia
#
# Authors: Alessio Treglia <quadrispro@ubuntu.com>
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
#
# Send a reply to the uploader once the build has finished.

import os
from subprocess import Popen, PIPE
from smtplib import SMTP
from email.parser import Parser


class DebomaticModule_Mailer:

    DEFAULT_OPTIONS = (
        'fromaddr',
        'smtphost',
        'smtpport',
        'authrequired',
        'smtpuser',
        'smtppass',
        'success',
        'failure')

    def __init__(self):
        self.dependencies = None

    def write_reply(self, template, buildlog, args):
        with open(template, 'r') as fd:
            substdict = dict(args)
            substdict['buildlog'] = buildlog
            substdict['fromaddr'] = self.fromaddr
            substdict['lintlog'] = 'No log'
            if self.lintlog:
                self.dependencies = ['Lintian']
                lintfile = os.path.join(self.resultdir, '%s.lintian'
                                        % args['package'])
                if os.path.isfile(lintfile):
                    with open(lintfile, 'r') as lintfd:
                        substdict['lintlog'] = lintfd.read()
            reply = fd.read() % substdict
        msg = Parser().parsestr(reply)
        return msg.as_string()

    def post_build(self, args):
        if not args['uploader']:
            return
        template = None
        uploader = args['uploader']
        self.resultdir = os.path.join(args['directory'], 'pool',
                                      args['package'])
        if args['opts'].has_section('mailer'):
            for opt in self.DEFAULT_OPTIONS:
                setattr(self, opt, args['opts'].get('mailer', opt))
            if args['opts'].has_option('mailer', 'lintlog'):
                self.lintlog = args['opts'].getint('mailer', 'lintlog')
        for filename in os.listdir(self.resultdir):
            if filename.endswith('.changes'):
                template = self.success
                break
        if not template:
            template = self.failure
        try:
            bp = '%(directory)s/pool/%(package)s/%(package)s.buildlog' % args
            buildlog_exc = Popen(['tail', '--lines=20', bp],
                                 stdout=PIPE).communicate()[0].decode('utf-8')
            msg = self.write_reply(template, buildlog_exc, args)
            self.smtp = SMTP(self.smtphost, int(self.smtpport))
            self.smtp.ehlo()
            if args['opts'].has_option('mailer', 'tls'):
                if args['opts'].getint('mailer', 'tls'):
                    self.smtp.starttls()
            if int(self.authrequired):
                self.smtp.login(self.smtpuser, self.smtppass)
            self.smtp.sendmail(self.fromaddr, uploader, msg)
            self.smtp.quit()
        except Exception as e:
            raise e
