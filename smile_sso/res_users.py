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


_logger = logging.getLogger('smile_sso')


def generate_random_password(length):
    """Generate password with an entropy per symbol equal to 6.5699 bits, i.e. for a 64-length password, 420 bits"""
    new_password = ''
    if length:
        chars = string.letters + string.digits + string.punctuation
        new_password = ''.join(choice(chars) for x in xrange(length))
    return new_password


class ResUsersExpiry(orm.Model):
    _name = 'res.users.expiry'
    _description = 'User Connection Expiry'
    _log_access = False

    _columns = {
        'user_id': fields.many2one("res.users", "User", required=True, ondelete="cascade", readonly=True),
        'login': fields.related('user_id', 'login', type="char", string="Login", store=True, select=True, readonly=True),
        'sso': fields.related('user_id', 'sso', type="boolean", string="SSO Authentification", store=True, select=True, readonly=True),
        'expiry_date': fields.datetime("Expiry Date", readonly=True),
    }

    def __init__(self, pool, cr):
        super(ResUsersExpiry, self).__init__(pool, cr)
        self._duration = 60 * 60 * 24 * 365  # TODO: indicate file where is defined

    def get_expiry_date(self):
        return (datetime.utcnow() + timedelta(seconds=self._duration)).strftime('%Y-%m-%d %H:%M:%S')


class ResUsers(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'sso': fields.boolean('SSO Authentification'),
    }

    _defaults = {
        'sso': True,
    }

    def sso_login(self, db, login, length=64, context=None):
        cr = pooler.get_db(db).cursor()
        try:
            cr.execute("SELECT u.id FROM res_users u LEFT JOIN res_users_expiry e ON u.id = e.user_id "
                       "WHERE u.login=%s AND u.active=TRUE AND u.sso=TRUE AND (e.expiry_date IS NULL OR e.expiry_date>=now() AT TIME ZONE 'UTC') "
                       "LIMIT 1", (login,))
            res = cr.dictfetchone()
            if not res:
                error_msg = "Server connection refused for the user [login=%s]" % login
                _logger.error(error_msg)
                return {'id': 0, 'password': ''}
            password = generate_random_password(length)
            cr.execute("UPDATE res_users SET password=%s WHERE login=%s AND sso=TRUE", (password, login))
            cr.commit()
            _logger.debug("Login of the user [login=%s]", login)
            res['password'] = password
            return res
        finally:
            cr.close()

    def sso_logout(self, db, login, context=None):
        cr = pooler.get_db(db).cursor()
        try:
            cr.execute("UPDATE res_users_expiry SET expiry_date=NULL WHERE login=%s AND sso=TRUE", (login,))
            cr.commit()
            _logger.debug("Logout of the user [login=%s]", login)
        finally:
            cr.close()

    def check(self, db, uid, passwd):
        if not passwd:
            error_msg = "No password authentication not supported!"
            _logger.error(error_msg)
            raise OpenERPException(error_msg, ('', '', ''))
        cr = pooler.get_db(db).cursor()
        try:
            cr.autocommit(True)
            if self._uid_cache.get(db, {}).get(uid) != passwd:
                cr.execute("SELECT u.id, u.password FROM res_users u LEFT JOIN res_users_expiry e ON u.id = e.user_id "
                           "WHERE u.id=%s AND u.password=%s AND u.active=TRUE "
                           "AND (e.expiry_date IS NULL OR e.expiry_date>=now() AT TIME ZONE 'UTC') "
                           "LIMIT 1", (uid, passwd))
                res = cr.fetchone()
                if not res:
                    error_msg = "Server session expired for the user [uid=%s]" % uid
                    _logger.error(error_msg)
                    raise OpenERPException(error_msg, ('', '', ''))
                self._uid_cache.setdefault(db, {}).update({uid: passwd})
            expiry_date = self.pool.get('res.users.expiry').get_expiry_date()
            cr.execute("SELECT u.login, e.login, u.sso FROM res_users u LEFT JOIN res_users_expiry e ON u.id = e.user_id "
                       "WHERE u.id=%s LIMIT 1", (uid,))
            user_info = cr.fetchone()
            if user_info[2]:
                if user_info[1]:
                    cr.execute("UPDATE res_users_expiry SET expiry_date=%s WHERE user_id=%s", (expiry_date, int(uid)))
                else:
                    cr.execute("INSERT INTO res_users_expiry (user_id, login, expiry_date) VALUES (%s, %s, %s AT TIME ZONE 'UTC')",
                               (int(uid), user_info[0], expiry_date))
                _logger.debug("Server session extended for the user [uid=%s]", uid)
        finally:
            cr.close()

    def create(self, cr, uid, vals, context=None):
        user_id = super(ResUsers, self).create(cr, uid, vals, context)
        self.pool.get('res.users.expiry').create(cr, uid, {'user_id': user_id}, context)
        return user_id

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('password') and not (uid == 1 and ids in (1, [1])) \
                and vals.get('sso', [user for user in self.browse(cr, uid, ids, context) if user.sso]):
            raise orm.except_orm(_('Operation Canceled'), _('You cannot modify password for user with SSO authentification!'))
        return super(ResUsers, self).write(cr, uid, ids, vals, context)
