# Deb-o-Matic - Mailer module
#
# Copyright (C) 2010 Alessio Treglia
# Copyright (C) 2015 Luca Falavigna
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
from glob import glob
from re import findall, DOTALL
from smtplib import SMTP
from email.parser import Parser


class DebomaticModule_Mailer:

    def __init__(self):
        self.after = ['Lintian']

    def write_reply(self, template, buildlog, package):
        lintianoutput = 'No log'
        with open(template, 'r') as fd:
            if self.lintian:
                lintfile = os.path.join(self.resultdir, '%s.lintian' % package)
                if os.path.isfile(lintfile):
                    with open(lintfile, 'r') as lintfd:
                        lintianoutput = lintfd.read()
            params = {'sender': self.sender,
                      'uploader': self.uploader,
                      'package': package,
                      'buildlog': buildlog,
                      'lintian': lintianoutput}
            reply = fd.read() % params
        msg = Parser().parsestr(reply)
        return msg.as_string().encode('utf-8')

    def post_build(self, args):
        if not args.uploader:
            return
        template = None
        self.uploader = args.uploader
        self.resultdir = os.path.join(args.directory, 'pool', args.package)
        if args.opts.has_section('mailer'):
            self.sender = args.opts.get('mailer', 'sender')
            self.server = args.opts.get('mailer', 'server')
            self.port = args.opts.getint('mailer', 'port')
            self.tls = args.opts.getboolean('mailer', 'tls')
            self.auth = args.opts.getboolean('mailer', 'authrequired')
            self.user = args.opts.get('mailer', 'user')
            self.passwd = args.opts.get('mailer', 'passwd')
            self.success = args.opts.get('mailer', 'success')
            self.failure = args.opts.get('mailer', 'failure')
            self.lintian = args.opts.getboolean('mailer', 'lintian')
        for filename in os.listdir(self.resultdir):
            if filename.endswith('.changes'):
                template = self.success
                break
        if not template:
            template = self.failure
        try:
            if args.xarchitecture:
                architecture = args.xarchitecture
            else:
                architecture = args.architecture
            bp = glob(os.path.join(args.directory, 'pool', args.package,
                                   '*_%s.build' % architecture))[0]
            with open(bp, 'r', encoding='utf8') as fd:
                if args.success:
                    data = findall('dpkg-buildpackage\n(.*)?\nBuild finished ',
                                   fd.read(), DOTALL)
                else:
                    data = findall('(.*)?\n┌─*┐\n│ Cleanup', fd.read(), DOTALL)
            try:
                if len(data[0]) > 20:
                    log = '\n'.join(data[0].split('\n')[-21:-1])
                else:
                    log = '\n'.join(data[0].split('\n'))
            except IndexError:
                return
            msg = self.write_reply(template, log, args.package)
            self.smtp = SMTP(self.server, self.port)
            self.smtp.ehlo()
            if args.opts.has_option('mailer', 'tls'):
                if args.opts.getboolean('mailer', 'tls'):
                    self.smtp.starttls()
            if self.auth:
                self.smtp.login(self.user, self.passwd)
            self.smtp.sendmail(self.sender, self.uploader, msg)
            self.smtp.quit()
        except Exception as e:
            raise e
