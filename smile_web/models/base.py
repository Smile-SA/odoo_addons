# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models

MODELS_TO_IGNORE = [
    'res.config.settings',
]


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(Base, self).fields_view_get(
            view_id, view_type, toolbar, submenu)
        if view_type == 'form' and self._name not in MODELS_TO_IGNORE:
            # Add automatically sheet element in arch to contourn a bug
            # with a chatter at right
            root = etree.fromstring(res['arch'])
            if root.find("sheet") is None:
                sheet = etree.Element('sheet')
                children = root.getchildren()
                for child in children[::-1]:
                    if child.tag in ('header', 'footer') or (
                            child.tag == 'div' and
                            child.attrib.get('class') == 'oe_chatter'):
                        continue
                    sheet.insert(0, child)
                root.insert(int(children[0].tag == 'header'), sheet)
            res['arch'] = etree.tostring(root)
        return res
