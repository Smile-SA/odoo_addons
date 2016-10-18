# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import api, fields, models

from odoo.addons.smile_scm.tools import cd


class VersionControlSystem(models.Model):
    _inherit = 'scm.vcs'

    cmd_revno = fields.Char('Get revision number', required=True)
    cmd_log = fields.Char('Get commit logs from last update', required=True)

    @api.multi
    def revno(self, directory, branch):
        self.ensure_one()
        with cd(directory):
            cmd_revno = self.cmd_revno % {'branch': branch}
            cmd = cmd_revno.split(' ')
            cmd.insert(0, self.cmd)
            revno = self.call(cmd)
            if self == self.env.ref('smile_scm.svn'):
                revno = revno.split(' ')[0]
            elif self != self.env.ref('smile_scm.git'):
                revno = literal_eval(revno)
            return revno.replace('\n', '')

    @api.multi
    def log(self, directory, last_revno=''):
        self.ensure_one()
        with cd(directory):
            if last_revno:
                cmd_log = self.cmd_log % {'last_revno': last_revno}
            else:
                cmd_log = 'log'
            cmd = cmd_log.split(' ')
            cmd.insert(0, self.cmd)
            return self.call(cmd)
