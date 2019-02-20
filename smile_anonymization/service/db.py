# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import shutil
import tempfile
import time

import openerp
from openerp import api, SUPERUSER_ID, tools
from openerp.modules.registry import Registry
from openerp.service import db

native_dump_db = db.dump_db
native_exp_dump = db.exp_dump


def new_dump_db(db_name, stream, backup_format='zip', anonymized=True):
    if anonymized:
        with Registry(db_name).cursor() as cr:
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
                with Registry(anon_db_name).cursor() as cr:
                    db._logger.info('ANONYMIZE DB: %s', anon_db_name)
                    cr.execute(anon_query)
            except Exception:
                db.exp_drop(anon_db_name)
            return native_dump_db(anon_db_name, stream, backup_format)
    return native_dump_db(db_name, stream, backup_format)

def new_exp_dump(db_name):
    with tempfile.TemporaryFile() as t:
        new_dump_db(db_name, t)
        t.seek(0)
        return t.read().encode('base64')

db.dump_db = new_dump_db
db.exp_dump = new_exp_dump
