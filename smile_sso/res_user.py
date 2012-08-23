# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

from datetime import datetime, timedelta
import logging
from random import choice
import string

from openerp.exceptions import DeferredException as OpenERPException
from osv import orm, fields
import pooler
from tools.translate import _


def generate_random_password(length):
    """Generate password with an entropy per symbol equal to 6.5699 bits, i.e. for a 64-length password, 420 bits"""
    new_password = ''
    if length:
        chars = string.letters + string.digits + string.punctuation
        new_password = ''.join(choice(chars) for x in xrange(length))
    return new_password


class User(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'expiry_date': fields.datetime("Expiry Date", readonly=True),
    }

    def __init__(self, pool, cr):
        super(User, self).__init__(pool, cr)
        self._duration = 60 * 60 * 24 * 365  # TODO: indicate file

    def get_expiry_date(self):
        return (datetime.utcnow() + timedelta(seconds=self._duration)).strftime('%Y-%m-%d %H:%M:%S')

    def sso_login(self, db, login, length=64, context=None):
        password = generate_random_password(length)
        expiry_date = self.get_expiry_date()
        set_clause = "date=now() AT TIME ZONE 'UTC', password=%s"
        params = [password]
        if expiry_date:
            set_clause += ', expiry_date=%s'
            params.append(expiry_date)
        where_clause = 'login=%s'
        params.append(login)
        cr = pooler.get_db(db).cursor()
        try:
            cr.execute("SELECT id, password FROM res_users WHERE login=%s AND password IS NOT NULL "
                       "AND active=TRUE AND (expiry_date IS NULL OR expiry_date>=now() AT TIME ZONE 'UTC') "
                       "LIMIT 1 FOR UPDATE NOWAIT", (login,))
            res = cr.dictfetchone()
            if not res or not res['password']:
                query = 'UPDATE res_users SET %s WHERE %s RETURNING id, password' % (set_clause, where_clause)
                cr.execute(query, params)
                res = cr.dictfetchone()
                cr.commit()
            if res:
                logging.getLogger('smile_sso').debug("Login of the user [login=%s]", login)
                return res
        finally:
            cr.close()

    def sso_logout(self, db, login, context=None):
        cr = pooler.get_db(db).cursor()
        try:
            cr.execute("UPDATE res_users SET password=NULL, expiry_date=NULL WHERE login=%s RETURNING id", (login,))
            res = cr.fetchone()
            cr.commit()
            if res:
                logging.getLogger('smile_sso').debug("Logout of the user [login=%s]", login)
                return True
        finally:
            cr.close()

    def check(self, db, uid, passwd):
        logger = logging.getLogger('smile_sso')
        if not passwd:
            error_msg = "No password authentication not supported!"
            logger.error(error_msg)
            raise OpenERPException(error_msg, ('', '', ''))
        cr = pooler.get_db(db).cursor()
        try:
            cr.autocommit(True)
            if self._uid_cache.get(db, {}).get(uid) != passwd:
                cr.execute('SELECT COUNT(1) FROM res_users WHERE id=%s AND password=%s AND '
                           'active=TRUE AND (expiry_date IS NULL OR expiry_date>=now()) LIMIT 1', (int(uid), passwd))
                res = cr.fetchone()[0]
                if not res:
                    error_msg = "Server session expired for the user [uid=%s]" % uid
                    logger.error(error_msg)
                    raise OpenERPException(error_msg, ('', '', ''))
                self._uid_cache.setdefault(db, {}).update({uid: passwd})
            cr.execute("UPDATE res_users SET expiry_date=%s AT TIME ZONE 'UTC' WHERE id=%s", (self.get_expiry_date(), int(uid)))
            logger.debug("Server session extended for the user [uid=%s]", uid)
        finally:
            cr.close()

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('password') and not (uid == 1 and ids in (1, [1])):
            raise orm.except_orm(_('Operation Canceled'), _('You cannot modify user password when the module smile_sso is installed!'))
        return super(User, self).write(cr, uid, ids, vals, context)
