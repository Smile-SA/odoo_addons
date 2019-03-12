# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    name = fields.Char(data_mask="'employee_' || id::text")
    name_related = fields.Char(data_mask="'resource_' || resource_id::text")
    birthday = fields.Date(data_mask="NULL")
    ssnid = fields.Char(data_mask="NULL")
    sinid = fields.Char(data_mask="NULL")
    identification_id = fields.Char(data_mask="NULL")
    gender = fields.Selection(data_mask="'other'")
    marital = fields.Selection(data_mask="NULL")
    work_phone = fields.Char(data_mask="NULL")
    mobile_phone = fields.Char(data_mask="NULL")
    work_email = fields.Char(data_mask="NULL")
    work_location = fields.Char(data_mask="NULL")
    notes = fields.Text(data_mask="NULL")
    parent_id = fields.Many2one(data_mask="NULL")
    coach_id = fields.Many2one(data_mask="NULL")
    job_id = fields.Many2one(data_mask="NULL")
    passport_id = fields.Char(data_mask="NULL")
