# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class Branch(models.Model):
    _inherit = 'scm.repository.branch'

    @api.one
    @api.depends('ansible_deployment_ids')
    def _get_ansible_deployments_count(self):
        self.ansible_deployments_count = len(self.ansible_deployment_ids)

    ansible_inventory_type_ids = fields.Many2many('ansible.inventory.type', string='Available environments')
    ansible_inventory_ids = fields.One2many('ansible.inventory', 'branch_id', 'Inventories')
    ansible_deployment_ids = fields.One2many('ansible.deployment', 'branch_id', 'Deployments', readonly=True)
    ansible_deployments_count = fields.Integer('Deployments count', compute='_get_ansible_deployments_count')

    @api.multi
    def update_ansible_inventories(self):
        def get_role_infos(obj):
            return {
                'role_id': obj.ansible_role_id.id,
                'origin_id': '%s,%s' % (obj._name, obj.id),
            }

        self.ensure_one()
        if not self.ansible_inventory_type_ids:
            raise UserError(_("Please indicate available environments"))
        for inventory_type in self.ansible_inventory_type_ids:
            inventories = self.ansible_inventory_ids.filtered(lambda inventory: inventory.inventory_type_id == inventory_type)
            existing_roles = inventories.mapped('role_id')
            roles_to_add = []
            package = self.version_id.package_ids.filtered(lambda package: package.os_id == self.os_id)
            if package.ansible_role_id and package.ansible_role_id not in existing_roles:
                roles_to_add.append(get_role_infos(package))
            for docker_image in self.mapped('link_ids.linked_image_id'):
                if docker_image.ansible_role_id and docker_image.ansible_role_id not in existing_roles:
                    roles_to_add.append(get_role_infos(docker_image))
            for inventory_vals in roles_to_add:
                inventory_vals['inventory_type_id'] = inventory_type.id
            self.write({'ansible_inventory_ids': [(0, 0, inventory_vals) for inventory_vals in roles_to_add]})
        return True

    @api.multi
    def open_deployment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ansible.deployment',
            'view_mode': 'form',
            'view_id': self.env.ref('smile_cd.view_ansible_deployment_popup').id,
            'res_id': False,
            'domain': [],
            'target': 'new',
            'context': {'default_branch_id': self.id},
        }
