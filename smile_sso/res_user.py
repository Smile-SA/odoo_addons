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

from datetime import datetime, timedelta
from random import choice
import string

from osv import osv, fields
import pooler
from service import security
from tools.translate import _

def generate_random_password(length):
    """Generate password with an entropy per symbol equal to 6.5699 bits, i.e. for a 64-length password, 420 bits"""
    new_password = ''
    if length:
        chars = string.letters + string.digits + string.punctuation
        new_password = ''.join(choice(chars) for _ in xrange(length))
    return new_password

def compute_expiry_date(duration):
    expiry_date = ''
    if duration:
        expiry_date = (datetime.now() + timedelta(seconds=duration)).strftime('%Y-%m-%d %H:%M:%S')
    return expiry_date

class User(osv.osv):
    _inherit = 'res.users'

    _columns = {
        'expiry_date': fields.datetime("Expiry Date", readonly=True),
    }

    def sso_login(self, db, login, length=64, duration=3600, context=None):
        password = generate_random_password(length)
        expiry_date = compute_expiry_date(duration)
        set_clause = 'date=now(), password=%s'
        params = [password]
        if expiry_date:
            set_clause += ', expiry_date=%s'
            params.append(expiry_date)
        where_clause = 'login=%s'
        params.append(login)
        cr = pooler.get_db(db).cursor()
        try:
            query = 'UPDATE res_users SET %s WHERE %s RETURNING id, password' % (set_clause, where_clause)
            cr.execute(query, params)
            res = cr.dictfetchone()
            cr.commit()
            if res:
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
                return True
        finally:
            cr.close()

    def check(self, db, uid, passwd):
        if not passwd:
            # empty passwords disallowed for obvious security reasons
            raise security.ExceptionNoTb('AccessDenied')
        if self._uid_cache.get(db, {}).get(uid) == passwd:
            return
        cr = pooler.get_db(db).cursor()
        try:
            cr.execute('SELECT COUNT(1) FROM res_users WHERE id=%s AND password=%s AND active=%s AND (expiry_date IS NULL OR expiry_date>=now())',
                        (int(uid), passwd, True))
            res = cr.fetchone()[0]
            if not res:
                raise security.ExceptionNoTb('AccessDenied')
            if self._uid_cache.has_key(db):
                ulist = self._uid_cache[db]
                ulist[uid] = passwd
            else:
                self._uid_cache[db] = {uid:passwd}
        finally:
            cr.close()

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('password') and not (uid == 1 and ids in (1, [1])):
            raise osv.except_osv(_('Operation Canceled'), _('You cannot modify user password when the module smile_sso is installed!'))
        return super(User, self).write(cr, uid, ids, vals, context)
User()
