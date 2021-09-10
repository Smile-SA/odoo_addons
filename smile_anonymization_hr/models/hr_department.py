# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    name = fields.Char(data_mask="'department_' || id::text")
    complete_name = fields.Char(data_mask="'department_' || id::text")
    parent_id = fields.Many2one(data_mask="NULL")
