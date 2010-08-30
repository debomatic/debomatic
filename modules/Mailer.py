# Deb-o-Matic - Contents module
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
import smtplib
from email.parser import Parser
from Debomatic import Options

class DebomaticModule_Mailer:

    DEFAULT_OPTIONS = (
        'smtphost',
        'smtpport',
        'authrequired',
        'smtpuser',
        'smtppass',
        'build_success_template',
        'build_failure_template',
        'fromaddr',
    )

    def __init__(self):
        # Disabled by default
        self.active = False
        if Options.has_section('mailer'):
            try:
                for opt in self.DEFAULT_OPTIONS:
                    setattr(self, opt, Options.get('mailer', opt))
                if self.authrequired:
                    pass                            # TODO
                else:
                    # Check the connection
                    self.smtp = smtplib.SMTP()
                    self.smtp.connect(self.smtphost, self.smtpport)
                    self.smtp.quit()                # Seems fine, closing for now
                self.active = True                  # Well configured, activate the module
            except:
                pass                                # TODO: something was wrong

    def post_build(self, args):
        if self.active and args['uploader']:
            template = None
            changes_file = None
            uploader = args['uploader']
            for filename in os.listdir(resultdir):  # Choose the template
                if filename.endswith('.changes'):   # Build was OK
                    template = self.build_success_template
                    break
            if not template:                        # Failed to build
                template = self.build_failure_template
            try:
                # Extract last lines from the buildlog
                buildlog_path = '%(directory)s/pool/%(package)s/%(package)s.buildlog' % args
                buildlog_exc = Popen(['tail', '-n20', buildlog_path], stdout=PIPE).communicate()[0]
                # Prepare the reply...
                msg = self._write_the_reply(template, buildlog_exc, args)
                # ...and send it!
                self.smtp.connect(self.smtphost, self.smtpport)
                self.smtp.sendmail(self.fromaddr, uploader, msg)
                self.smtp.quit()                    # Close the connection
            except:
                pass                                # TODO
        else:
            raise Exception("Something has gone wrong")

    def _write_the_reply(self, template, buildlog, args):
        fp = open(template, 'r')
        substdict = dict(args)
        substdict['buildlog'] = buildlog
        substdict['fromaddr'] = self.fromaddr
        reply = fp.read() % substdict
        fp.close()
        msg = Parser().parsestr(reply)
        return msg.as_string()
