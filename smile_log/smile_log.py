# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields


class SmileLog(osv.osv):
    _name = 'smile.log'
    _description = 'Smile Logs'
    _rec_name = 'message'
    _log_access = False

    _order = 'log_date desc'

    def __init__(self, pool, cr):
        super(SmileLog, self).__init__(pool, cr)
        cr.execute("select relname from pg_class where relname='smile_log_seq'")
        res = cr.fetchone()
        if not res:
            cr.execute("create sequence smile_log_seq")
        else:
            from db_handler import SmileDBLogger
            logger = SmileDBLogger(cr.dbname, '', 0, 0)
            logger.info('OpenERP server start')

    def _get_user_name(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        user_obj = self.pool.get('res.users')
        user_id_to_name = {}
        for log in self.browse(cr, uid, ids, context):
            if log.log_uid not in user_id_to_name:
                if user_obj.exists(cr, uid, log.log_uid, context):
                    name = user_obj.read(cr, uid, log.log_uid, ['name'], context)['name']
                    user_id_to_name[log.log_uid] = "%s [%s]" % (name, log.log_uid)
                else:
                    user_id_to_name[log.log_uid] = "[%s]" % (log.log_uid,)
            result[log.id] = user_id_to_name[log.log_uid]
        return result

    def _get_res_name(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        res_to_name = {}
        for log in self.browse(cr, uid, ids, context):
            res_key = (log.model_name, log.res_id)
            result[log.id] = "%s,%s" % res_key
            if log.model_name and log.res_id:
                if res_key in res_to_name:
                    result[log.id] = res_to_name[res_key]
                else:
                    if self.pool.get(log.model_name) and self.pool.get(log.model_name).exists(cr, uid, log.res_id, context):
                        name = self.pool.get(log.model_name).name_get(cr, uid, log.res_id, context)
                        if name and name[0]:
                            res_to_name[(log.model_name, log.res_id)] = name[0][1]
                            result[log.id] = name[0][1]
        return result

    _columns = {
        'log_date': fields.datetime('Date', readonly=True),
        'log_uid': fields.integer('User', readonly=True),
        'log_user_name': fields.function(_get_user_name, method=True, string='User', type='char', size=256),
        'log_res_name': fields.function(_get_res_name, method=True, string='Ressource name', type='char', size=256),

        'model_name': fields.char('Model name', size=64, readonly=True),
        'res_id': fields.integer('Ressource id', readonly=True, group_operator="count"),

        'pid': fields.integer('Pid', readonly=True, group_operator="count"),
        'level': fields.char('Level', size=16, readonly=True),
        'message': fields.text('Message', readonly=True),
    }
SmileLog()
