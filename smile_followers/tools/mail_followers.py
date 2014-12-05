# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Toyota Industrial Equipment SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api
from openerp.tools.func import wraps


def AddFollowers(fields=['partner_id']):
    def decorator(original_class):
        original_class.create = api.model(add_followers(fields)(original_class.create))
        original_class.write = api.multi(add_followers(fields)(original_class.write))
        return original_class
    return decorator


def add_followers(fields=['partner_id']):
    def decorator(create_or_write):
        @wraps(create_or_write)
        def wrapper(self, vals):
            follower_obj = self.env['mail.followers']
            for field in fields:
                # Remove followers linked to old partner
                if vals.get(field) and self.ids:
                    follower_obj.search([
                        ('res_model', '=', self._name),
                        ('res_id', 'in', self.ids),
                        ('partner_id.parent_id', 'in', [getattr(r, field).id for r in self])
                    ]).unlink()
            res = create_or_write(self, vals)
            for field in fields:
                # Add followers linked to new partner
                if vals.get(field):
                    record_ids = self.ids or [res.id]
                    notification_filter = lambda c: self._name in [m.model for m in c.notification_model_ids]
                    for contact in self.env['res.partner'].browse(vals[field]).child_ids.filtered(notification_filter):
                        for record_id in record_ids:
                            follower_obj.sudo().create({
                                'res_model': self._name,
                                'res_id': record_id,
                                'partner_id': contact.id,
                            })
            return res
        return wrapper
    return decorator
