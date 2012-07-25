# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http: //www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

import os.path
import re

from osv import fields, osv
from tools.translate import _


class smile_dir_scanner_template(osv.osv):
    _name = 'smile_dir_scanner.template'
smile_dir_scanner_template()


class smile_dir_scanner_file(osv.osv):
    _name = 'smile_dir_scanner.file'

    _order = 'id desc'

    _columns = {
        'create_date': fields.datetime('Create date', readonly=True),
        'template_id': fields.many2one('smile_dir_scanner.template', 'Template', readonly=True),
        'name': fields.char('Filename', size=64, readonly=True),
        'full_path': fields.char('Full path', size=256, readonly=True),
        'computed': fields.boolean('Computed', readonly=True),
        'hash': fields.char('Hash', size=128, readonly=True),
    }

smile_dir_scanner_file()

HASH_CHECK = [
    ('none', 'none'),
    ('md5', 'md5'),
    ('sha1', 'sha1'),
    ('sha224', 'sha224'),
    ('sha256', 'sha256'),
    ('sha384', 'sha384'),
    ('sha512', 'sha512'),
]


class smile_dir_scanner_template2(osv.osv):
    _inherit = 'smile_dir_scanner.template'

    _columns = {
        'name': fields.char('Name', size=64, required=True,),
        'directory': fields.char('Directory to scan', size=256, required=True,),
        'recursive_search': fields.boolean('Recursive search', required=True, help="If True, search will browse through sub-directories."),
        'file_regex': fields.char('Regex to match filename', size=128,),
        'file_ids': fields.one2many('smile_dir_scanner.file', 'template_id', "Matched files", readonly=True),
        'cron_id': fields.many2one('ir.cron', 'Scheduled Action'),
        'hash_check': fields.selection(HASH_CHECK, "Hash Check", help="Used to check if the file was already importe"),
    }

    _defaults = {
        'hash_check': 'none',
    }

    # Possible improvment: use hashlib library to compute md5 key of each file
    # and add an option to not import the same file several time
    # a=file('/home/xafer/Téléchargements/TOS-All-r53616-V4.1.2.zip', 'r')
    # print hashlib.md5(a.read()).hexdigest()
    # 7a883f11b28d815e94e1f7a7e99f7dc4
    def search_directory(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for template in self.browse(cr, uid, ids, context):
            hash_check = template.hash_check != 'none'
            known_hashes = set([])
            if hash_check:
                file_ids = self.pool.get('smile_dir_scanner.file').search(cr, uid, [('template_id', '=', template.id)])
                for file in self.pool.get('smile_dir_scanner.file').browse(cr, uid, file_ids, context):
                    known_hashes.add(file.hash)

            if template.directory and os.path.isdir(template.directory):
                re_to_match = re.compile(template.file_regex or '')

                matched_files = []
                for directory in os.walk(template.directory):
                    for filename in directory[2]:
                        if re_to_match.match(filename):
                            #directory[0] contains the current path
                            matched_files.append((directory[0], filename))
                    if not template.recursive_search:
                        # only search the tree root: that's done after the first iteration
                        break
                for file in matched_files:
                    hash = ''
                    if hash_check:
                        file_content = file(file[0] + '/' + file[1], 'r')
                        hash = getattr(hashlib, template.hash_check)(file_content.read()).hexdigest()
                        file_content.close()
                        if hash in known_hashes:
                            continue
                    self.pool.get('smile_dir_scanner.file').create(cr, uid, {
                        'template_id': template.id,
                        'name': file[1],
                        'full_path':  file[0],
                        'hash': hash,
                    })
            else:
                raise osv.except_osv(_('Error !'), _("Directory scanner: %s's directory (%s) is not valid !") % (template.name, template.directory,))
        return True

    def create_cron(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for template in self.browse(cr, uid, ids, context):
            if not template.cron_id:
                vals = {
                    'name': "Dir. Scan. " + template.name,
                    'user_id': 1,
                    'model': self._name,
                    'function': 'search_directory',
                    'args': '(%d, )' % template.id,
                    'interval_type': 'days',
                    'numbercall': -1,
                }
                cron_id = self.pool.get('ir.cron').create(cr, uid, vals)
                template.write({'cron_id': cron_id})
        return True

smile_dir_scanner_template()
