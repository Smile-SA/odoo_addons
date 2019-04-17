# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import models
from openerp.osv import fields


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    # Needs to set old columns instead of new fields for this model, or
    # hr.employee creation is not possible. See models._create.
    _columns = {
        'name': fields.char(
            data_mask="'resource_' || id::text WHERE resource_type = 'user'"),
        'code': fields.char(data_mask="NULL"),
    }
