# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.modules.registry import Registry

native_setup_models = Registry.setup_models


def new_setup_models(self, cr):
    # Force to call unlink method at removal of remote object linked
    # by a fields.many2one with ondelete='cascade'
    native_setup_models(self, cr)
    for RecordModel in self.models.values():
        for fieldname, field in RecordModel._fields.items():
            if field.type == 'many2one' and field.ondelete and \
                    field.ondelete.lower() == 'cascade':
                if field.comodel_name.startswith('mail.'):
                    continue
                CoModel = self.get(field.comodel_name)
                if not hasattr(CoModel, '_cascade_relations'):
                    setattr(CoModel, '_cascade_relations', {})
                CoModel._cascade_relations.setdefault(
                    RecordModel._name, set()).add(fieldname)


Registry.setup_models = new_setup_models
