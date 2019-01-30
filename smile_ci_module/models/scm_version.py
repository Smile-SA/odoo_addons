# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .scm_repository_branch_module import LICENSES


class ScmVersion(models.Model):
    _inherit = 'scm.version'

    default_license = fields.Selection(LICENSES)
