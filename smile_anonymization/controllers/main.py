
import time


from openerp import SUPERUSER_ID
from openerp import pooler
from openerp.service.web_services import db, _logger
from openerp.addons.web.controllers.main import Database
from openerp.addons.web import http

openerpweb = http


class AnonymizeDatabase(Database):

    def backup_anonymized(self, req, backup_db):
        dbs = db
        cr = pooler.get_db(backup_db).cursor()
        fields_obj = pooler.get_pool(cr.dbname).get('ir.model.fields')
        anon_query = fields_obj.get_anonymization_query(cr, SUPERUSER_ID)
        if not anon_query:
            _logger.info("No data to anonymize in database `%s`.", backup_db)
        else:
            _logger.info('Anonymize and dump database `%s`.', backup_db)
            anon_db_name = '%s_anon_%s' % (
                backup_db, time.strftime('%Y%m%d_%H%M%S'))
            dbs = db(backup_db)
            dbs.exp_duplicate_database(cr.dbname, anon_db_name)
            # Process
            _logger.info('ANONYMIZE DB: %s', anon_db_name)
            cr = pooler.get_db(anon_db_name).cursor()
            cr.execute(anon_query)
            cr.commit()
            backup_db = anon_db_name
        return backup_db, dbs

    @openerpweb.httprequest
    def backup(self, req, backup_db, backup_pwd, token):
        backup_db, dbs = self.backup_anonymized(req, backup_db)
        res = super(AnonymizeDatabase, self).backup(req, backup_db, backup_pwd, token)
        dbs.exp_drop(backup_db)
        return res
