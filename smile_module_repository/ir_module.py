# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

import logging
from os import listdir, path, walk
import re
import shutil
from subprocess import call
import tempfile
import time

from openerp.osv import orm, fields
from openerp.tools import config
from openerp.tools.translate import _

from tools import cd

_logger = logging.getLogger(__package__)


class IrModuleVCS(orm.Model):
    _name = 'ir.module.vcs'
    _description = 'Version Control System'

    _columns = {
        'name': fields.char('Name', size=12, required=True),
        'cmd': fields.char('Command', size=3, required=True),
        'cmd_clone': fields.char('Get', size=12, required=True),
        'cmd_pull': fields.char('Update', size=12, required=True),
    }

    _sql_constraints = [
        ('unique_cmd', 'UNIQUE(cmd)', 'VCS must be unique'),
    ]


class IrModuleVersion(orm.Model):
    _name = 'ir.module.version'
    _description = 'OpenERP Version'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=12, required=True),
    }

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'OpenERP version must be unique'),
    ]


class IrModuleRepository(orm.Model):
    _name = 'ir.module.repository'
    _description = 'Modules Repository'
    _inherit = ['mail.thread']

    def _get_dirname(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, '')
        match = re.compile('([/@.])')
        for rep in self.browse(cr, uid, ids, context):
            if rep.directory:
                res[rep.id] = '%s_%s' % (rep.vcs_id.cmd, match.sub('_', rep.directory.split(':')[-1]))
        return res

    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'version_id': fields.many2one('ir.module.version', 'OpenERP Version', required=True, ondelete="restrict"),
        'vcs_id': fields.many2one('ir.module.vcs', 'Version Control System', required=True, ondelete="restrict",
                                  readonly=True, states={'draft': [('readonly', False)]}),
        'directory': fields.char('Directory', size=256, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'relpath': fields.function(_get_dirname, method=True, type='char', size=128, string="Relative Path", store={
            'ir.module.repository': (lambda self, cr, uid, ids, context=None: ids, ['directory'], 5),
        }),
        'state': fields.selection([('draft', 'Not cloned'), ('done', 'Cloned')], "State", required=True, readonly=True),
        'last_update': fields.datetime("Last Update", readonly=True),
        'active': fields.boolean("Active"),
    }

    _defaults = {
        'state': 'draft',
    }

    _sql_constraints = [
        ('unique_directory', 'UNIQUE(directory)', 'Directory must be unique'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        for rep in self.browse(cr, uid, ids, context):
            result.append((rep.id, '%s - %s' % (rep.version_id.name, rep.name)))
        return result

    @property
    def _parent_path(self):
        parent_path = config.get('repositories_path') or tempfile.gettempdir()
        if not path.isdir(parent_path):
            raise orm.except_orm(_('Error'), _("%s doesn't exist or is not a directory") % parent_path)
        return parent_path

    @staticmethod
    def _call(cmd):
        command = ' '.join(cmd)
        try:
            call(cmd)
            _logger.info('%s SUCCEEDED' % command)
        except Exception, e:
            msg = '%s FAILED - Error: %s'
            _logger.error(msg % (command, e))
            raise orm.except_orm(_('Error'), _(msg) % (command, e))

    def clone(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        with cd(self._parent_path):
            for rep in self.browse(cr, uid, ids, context):
                if rep.state != 'draft':
                    raise om.except_orm(_('Error'), _('You cannot clone a repository already cloned'))
                vcs = rep.vcs_id
                IrModuleRepository._call([vcs.cmd, vcs.cmd_clone, rep.directory, rep.relpath])
        self.extract_modules(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'active': True, 'state': 'done', 'last_update': time.strftime('%Y-%m-%d %H:%M:%S')}, context)

    def pull(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for rep in self.browse(cr, uid, ids, context):
            if rep.state == 'draft':
                raise om.except_orm(_('Error'), _('You cannot pull a repository not cloned'))
            with cd(path.join(self._parent_path, rep.relpath)):
                vcs = rep.vcs_id
                IrModuleRepository._call([vcs.cmd, vcs.cmd_pull])
        self.extract_modules(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'last_update': time.strftime('%Y-%m-%d %H:%M:%S')}, context)

    def extract_modules(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for rep in self.browse(cr, uid, ids, context):
            modules = self._extract_modules(cr, uid, rep, context)
            product_obj.create_or_update(cr, uid, modules, context)
        return True

    def _extract_modules(self, cr, uid, rep, context=None):
        modules = []
        for oerp_file in IrModuleRepository._get_oerp_files(path.join(self._parent_path, rep.relpath)):
            module_infos = self._get_module_infos(oerp_file)
            module_infos['repository_id'] = rep.id
            modules.append(module_infos)
        return modules

    @staticmethod
    def _get_oerp_files(dirpath):
        oerp_files = []
        if path.isdir(dirpath):
            for root, dirs, files in walk(dirpath):
                for filename in ('__openerp__.py', '__terp__.py'):
                    if filename in files:
                        oerp_files.append(path.join(root, filename))
        return oerp_files

    def _get_module_icon(self, modulepath):
        if path.isdir(modulepath):
            icon_path = path.join(self._parent_path, 'static', 'src', 'img', 'icon.png')
            if path.isfile(icon_path):
                with open(icon_path, 'rb') as icon_file:
                    return icon_file.read().encode('base64')
        return False

    def _get_module_infos(self, filepath):
        openerp_infos = {}
        if path.isfile(filepath):
            with open(filepath) as openerp_file:
                openerp_infos.update(eval(openerp_file.read()))
            module_path = path.dirname(filepath)
            openerp_infos.update({
                'variants': module_path,
                'name': path.basename(module_path),
                'shortdesc': openerp_infos['name'],
                'image': self._get_module_icon(module_path),
                'active': True,
                'is_module': True,
            })
        return openerp_infos

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for rep in self.browse(cr, uid, ids, context):
            try:
                shutil.rmtree(path.join(self._parent_path, rep.relpath))
            except:
                pass
        return super(IrModuleRepository, self).unlink(cr, uid, ids, context)
