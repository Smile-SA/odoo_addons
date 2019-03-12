# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import shutil
import tempfile
import time


from odoo import api, SUPERUSER_ID, tools
from odoo.modules.registry import Registry
from odoo.service import db

native_dump_db = db.dump_db
native_exp_dump = db.exp_dump


class NewDbDump:
    def __init__(self, db_name, stream, backup_format='zip'):
        self._db_name = db_name
        self._iterator = native_dump_db(db_name, stream, backup_format)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            db.exp_drop(self._db_name)
            raise


@db.check_db_management_enabled
def new_dump_db(db_name, stream, backup_format='zip', anonymized=True):
    if anonymized:
        with Registry.new(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            anon_query = env['ir.model.fields'].get_anonymization_query()
        if not anon_query:
            db._logger.info("No data to anonymize in database `%s`.", db_name)
        else:
            db._logger.info('Anonymize and dump database `%s`.', db_name)
            anon_db_name = '%s_anon_%s' % (
                db_name, time.strftime('%Y%m%d_%H%M%S'))
            db.exp_duplicate_database(db_name, anon_db_name)
            try:
                if backup_format == 'zip':
                    # To avoid to archive filestore
                    # with non-anonymized attachments
                    anon_fs = tools.config.filestore(anon_db_name)
                    shutil.rmtree(anon_fs, ignore_errors=True)
                with Registry.new(anon_db_name).cursor() as cr:
                    db._logger.info('ANONYMIZE DB: %s', anon_db_name)
                    cr.execute(anon_query)
            except Exception:
                db.exp_drop(anon_db_name)
            return NewDbDump(anon_db_name, stream, backup_format)
    return native_dump_db(db_name, stream, backup_format)


@db.check_db_management_enabled
def new_exp_dump(db_name, backup_format, anonymized=False):
    with tempfile.TemporaryFile(mode='w+b') as t:
        new_dump_db(db_name, t, backup_format, anonymized)
        t.seek(0)
        return base64.b64encode(t.read()).decode()


db.dump_db = new_dump_db
db.exp_dump = new_exp_dump
