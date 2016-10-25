# -*- coding: utf-8 -*-

import logging
import os
from subprocess import CalledProcessError

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..tools import cd, check_output_chain

_logger = logging.getLogger(__name__)


class VersionControlSystem(models.Model):
    _name = 'scm.vcs'
    _description = 'Version Control System'

    name = fields.Char(required=True)
    cmd = fields.Char('Command', size=3, required=True)
    cmd_clone = fields.Char('Clone', required=True)
    cmd_pull = fields.Char('Pull', required=True)
    default_branch = fields.Char('Default branch')

    _sql_constraints = [
        ('unique_cmd', 'UNIQUE(cmd)', 'VCS must be unique'),
    ]

    @api.model
    def call(self, cmd):
        command = ' '.join(cmd)
        try:
            result = check_output_chain(cmd)
            _logger.info('%s SUCCEEDED' % command)
            return result
        except CalledProcessError, e:
            raise UserError(_('%s FAILED\nfrom %s\n\n%s')
                            % (command, os.getcwd(), e.output))

    @api.multi
    def clone(self, directory, branch, url):
        self.ensure_one()
        localdict = {'url': url, 'branch': branch or self.default_branch}
        cmd_clone = self.cmd_clone % localdict
        cmd = cmd_clone.split(' ')
        cmd.insert(0, self.cmd)
        cmd.append(directory)
        self.call(cmd)
        return True

    @api.multi
    def pull(self, directory):
        self.ensure_one()
        cmd = self.cmd_pull.split(' ')
        cmd.insert(0, self.cmd)
        with cd(directory):
            self.call(cmd)
        return True
