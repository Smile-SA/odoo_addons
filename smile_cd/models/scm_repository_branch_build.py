# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.addons.smile_docker.tools import with_new_cursor


class Build(models.Model):
    _inherit = 'scm.repository.branch.build'

    use_in_ci = fields.Boolean(related='branch_id.use_in_ci', readonly=True)

    @api.multi
    def open_deployment_wizard(self):
        self.ensure_one()
        action = self.branch_id.open_deployment_wizard()
        action['context']['default_build_id'] = self.id
        return action

    @api.one
    def _set_build_result(self):
        super(Build, self)._set_build_result()
        try:
            self._auto_deploy()
        except Exception as e:
            msg = _('Auto deployment failed\n\n%s') % e
            self._post_error_message(msg)

    @api.one
    @with_new_cursor(False)
    def _post_error_message(self, msg):
        self.message_post(msg)

    @api.one
    def _auto_deploy(self):
        branch = self.branch_id
        if branch.use_branch_tmpl_to_deploy:
            branch = branch.branch_tmpl_id
        for rule in branch.ansible_deployment_rule_ids:
            if self.result in rule.build_result:
                date_planned = rule.compute_date_planned() or \
                    fields.Datetime.now()
                self.env['ansible.deployment'].update_or_create({
                    'branch_id': self.branch_id.id,
                    'build_id': self.id,
                    'revno': self.revno,
                    'inventory_type_id': rule.inventory_type_id.id,
                    'date_planned': date_planned,
                })
