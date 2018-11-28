# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestGeneralRead(TransactionCase):

    def test_check_general_read(self):
        """ I test all search and reads.
        """
        errors = []
        models = self.env['ir.model'].search([])
        for model in models:
            RecordModel = self.env[model.model]
            if not getattr(RecordModel, '_auto', True):
                # Exclude abstract models
                continue
            try:
                with self.env.cr.savepoint():
                    test_type = 'count'
                    if RecordModel.search_count([]):
                        test_type = 'search_limit'
                        record = RecordModel.search([], limit=1)
                        test_type = 'read_one'
                        record.read()
                        test_type = 'search_all'
                        records = RecordModel.search([])
                        test_type = 'read_all'
                        records.read()
                        if RecordModel._transient:
                            continue
                        test_type = 'name_get'
                        records.name_get()
            except Exception as e:
                err_info = (model.model, test_type, repr(e))
                errors.append(err_info)
        err_details = "\n".join(
            ["(%s, %s): %s" % (model, view_type, err)
             for model, view_type, err in errors])
        error_msg = "Error in search/read for model/test " \
            "and error:\n%s" % err_details
        self.assertEquals(len(errors), 0, error_msg)
