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

from openerp.osv import fields, orm
import time
from openerp.tools.translate import _
from datetime import datetime
import re
from openerp import tools

import cStringIO
import xlrd

import openerp.pooler as pooler
from openerp import addons
import csv
import os

FIELD2SKIP = (fields.one2many,
              fields.many2many,
              fields.related,
              fields.binary,
              fields.function,
)

RUN_STATES = [('draft', 'Draft'),
              ('in_progress', 'In progress'),
              ('done', 'Done'),
              ('template', 'Template'),
]

IMPORT_TYPES = [('import_data', 'Import data'),
              ('script', 'Script'),
]

FILE_EXTENSIONS = [
                   ('csv', 'CSV'),
                   ('xls', 'Excel 2003'),
                   ('xlsx', 'Excel 2007/2010'),
]

FILE_DELIMTERS = [(',', ','),
                  (';', ';')
]

def convert_csv_import(cr, module, fname, csvcontent, idref=None, mode='init', noupdate=False, context=None, delimiter=','):
    '''Import csv file :
        quote: "
        encoding: utf-8'''
    if not idref:
        idref = {}
    model = ('.'.join(fname.split('.')[:-1]).split('-'))[0]
    #remove folder path from model
    head, model = os.path.split(model)

    pool = pooler.get_pool(cr.dbname)

    input = cStringIO.StringIO(csvcontent)  #FIXME
    reader = csv.reader(input, quotechar='"', delimiter=delimiter)
    fields = reader.next()
    fname_partial = ""

    uid = 1
    datas = []
    for line in reader:
        if (not line) or not reduce(lambda x, y: x or y, line)  :
            continue
        try:
            datas.append(map(lambda x: tools.misc.ustr(x), line))
        except:
            print "Cannot import the line: %s", line
    nb_imported_items, logs = pool.get(model).import_data_custom(cr, uid, fields, datas, mode, module, noupdate, filename=fname_partial, context=context)
    if not (logs or nb_imported_items):
        nb_imported_items = len(datas)

    return len(datas), nb_imported_items, logs


class ImportDataRun(orm.Model):

    _name = 'import.data.run'

    _columns = {
            'name': fields.char('Name', size=64),
            'state': fields.selection(RUN_STATES, "State", readonly=True),
            'start_date': fields.datetime('Start date', readonly=True),
            'last_import_date': fields.datetime('Last import date', readonly=True),
            'done_date': fields.datetime('Done date', readonly=True),
            'extract_file_date': fields.datetime('Extract files date', required=False, help='Last date of extracting file'),
            'object_ids': fields.one2many('import.data.run.object', 'run_id', 'Objects', ondelete='cascade'),
            'template_ok':fields.boolean('Is a template'),
            'template_run_id':fields.many2one('import.data.run', 'Template', domain=[('template_ok', '=', True)]),
            # LOGS
            'log_ids':fields.one2many('import.data.log', 'run_id', 'Run logs', ondelete='cascade', readonly=True, domain=[('level', '!=', 'success')],),
            'success_log_ids':fields.one2many('import.data.log', 'run_id', 'Success logs', ondelete='cascade', domain=[('level', '=', 'success')], readonly=True),
            'warning_log_ids':fields.one2many('import.data.log', 'run_id', 'Warning logs', ondelete='cascade', domain=[('level', '=', 'warning')], readonly=True),
            'error_log_ids':fields.one2many('import.data.log', 'run_id', 'Error logs', ondelete='cascade', domain=[('level', '=', 'error')], readonly=True),
            # Configuration
            # Run configuration
            'run_path':fields.char('Run path', size=512, readonly=True),
            'run_data_path':fields.char('Run data path', size=512, readonly=True),
            'keep_logs_ok':fields.boolean('Keep logs'),
            'config_yml_file_path': fields.char('Config file', size=128, required=False),
            'import_partial': fields.boolean(u'Import partielle'),
            # Template configuration
            'root_path':fields.char('Root path of the template run', size=512, readonly=True),
            'config_path':fields.char('Config path of template run', size=512, readonly=True),
            'templates_path':fields.char('Object template files', size=512, readonly=True),
            'runs_path':fields.char('Root of runs', size=512, readonly=True),
            'ir_model_data_ref':fields.char('IR model data ref', size=512, readonly=True),
            # validation result
            'files_validaiton_ok':fields.boolean('Files validated', readonly=True),
            'files_validaiton_date':fields.datetime('File validation date', readonly=True),
            'note': fields.text('Notes'),
            }

    _defaults = {
        'state':'draft',
    }

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The name of the run must be unique!'),
    ]

    def close_run(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state':'done'}, context)
        return True

    def _check_state(self, cr, uid, ids, context=None):
        for run in self.browse(cr, uid, ids, context):
            res_ids = []
            if not run.template_ok :
                res_ids = self.search(cr, uid, [('state', '=', 'in_progress'),
                                                ('template_ok', '=', False),
                                                ('template_run_id', '=', run.template_run_id.id),
                                                ('id', '!=', run.id)],
                                                context=context)
            if res_ids:
                return False
        return True

    _constraints = [ (_check_state,
                      "You can't have more than one started run for the same template. Please finish in progress run",
                      [_('State')]),
    ]
    def validate_template(self, cr, uid, ids, context=None):
        ir_model_data_obj = self.pool.get('ir.model.data')
        for run in self.browse(cr, uid, ids, context):
            ad_paths = addons.get_module_path('smile_import_data')
            newpath = ad_paths + '/runs/' + run.name + '/'
            # Create data folder
            if not os.path.exists(newpath):
                os.makedirs(newpath)
                os.makedirs(newpath + 'config/')
                os.makedirs(newpath + 'templates/')
            else:
                raise orm.except_orm(_('Error'), _("The folder %s must be removed or please set another name to your Run template") % run.name)

            ir_model_data_obj.create(cr, uid, {
                            'name': 'run_%s' % (run.id),
                            'model': 'import.data.run',
                            'module':'smile_import_data',
                            'res_id':run.id,
                            'noupdate':True,
                            }, context=context)


            self.write(cr, uid, ids, {'name':run.name,
                                      'root_path':newpath,
                                      'config_path':newpath + 'config/',
                                      'templates_path':newpath + 'templates/',
                                      'runs_path':newpath + 'runs/',
                                      'template_ok':True,
                                      'state':'template',
                                      'ir_model_data_ref':'smile_import_data.run_%s' % (run.id),
                                      },
                                      context=context)
        return True

    def delete_logs(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        log_obj = self.pool.get('import.data.log')
        log_ids = log_obj.search(cr, uid, [('run_id', 'in', ids)], context=context)
        log_obj.unlink(cr, uid, log_ids, context)
        return True

    def button_start_run(self, cr, uid, ids, context=None):
        '''
            Start the run by creating new folter with 
            name = "NameRun_AAAA_MM_JJ",
            change the state of the run to 
            Start
        '''
        for run in self.browse(cr, uid, ids, context):
            run_name = "%s_%s" % (run.template_run_id.name, time.strftime('%Y_%m_%d_%H_%M'))

            newpath = run.template_run_id.runs_path + run_name + '/'
            if not os.path.exists(newpath): os.makedirs(newpath)

            # Create data folder
            data_folder = newpath + 'data/'
            if not os.path.exists(data_folder): os.makedirs(data_folder)

            self.write(cr, uid, ids, {'name':run_name,
                                      'state':'in_progress',
                                      'run_path':newpath,
                                      'run_data_path':data_folder,
                                      'start_date':time.strftime('%Y-%m-%d %H:%M')
                                      },
                                      context=context)
        return True

    def button_init_run(self, cr, uid, ids, context=None):
        """
            Charge the configuration of the from a run template
        """
        object_obj = self.pool.get('import.data.run.object')

        for run in self.browse(cr, uid, ids, context):
            default = {'run_id':run.id}
            for obj in run.object_ids:
                object_obj.unlink(cr, uid, obj.id, context)

            for obj in run.template_run_id.object_ids:
                object_obj.copy(cr, uid, obj.id, default, context=context)

        return True

    def button_import(self, cr, uid, ids, context=None):
        '''
            Start import of all files
        '''
        # TODO not yet tested
        object_obj = self.pool.get('import.data.run.object')

        for run in self.browse(cr, uid, ids, context):
            context['import_partial'] = run.import_partial
            object_ids = [obj.id for obj in run.object_ids]
            object_obj.import_file(cr, uid, object_ids, context)

        return True

    def button_convert_file(self, cr, uid, ids, context=None):
        '''
            Convert files on the expended format
        '''
        # TODO implemente this method
        return True

    def check_file_validation(self, cr, uid, ids, context=None):
        '''
            Start validation of all files specified on the run 
        '''
        object_obj = self.pool.get('import.data.run.object')
        for run in self.browse(cr, uid, ids, context):
            if not run.keep_logs_ok:
                self.delete_logs(cr, uid, run.id, context)
            object_ids = [obj.id for obj in run.object_ids]
            object_obj.check_file_validation(cr, uid, object_ids, context)

        return True

    def initialize_objects(self, cr, uid, ids, context=None):
        object_obj = self.pool.get('import.data.run.object')
        for run in self.browse(cr, uid, ids, context):
            object_ids = [obj.id for obj in run.object_ids if not obj.manage_manually_ok]
            object_obj.initialize_objects(cr, uid, object_ids, context)

        return True

    def init_from_config_file(self, cr, uid, ids, context=None):
        object_obj = self.pool.get('import.data.run.object')
        for run in self.browse(cr, uid, ids, context):
            for obj in run.object_ids:
                object_obj.unlink(cr, uid, obj.id, context)
            if not run.config_yml_file_path:
                raise orm.except_orm('Error', _(u"Veuillez completer le chemin du fichier de configuration"))
            yaml_file = run.config_path + run.config_yml_file_path
            if not os.path.exists(yaml_file):
                raise orm.except_orm('Error', _(u"Le chemin  %s est non valide.") % yaml_file)
            tools.convert_yaml_import(cr, 'smile_import_data', file(yaml_file), 0, mode='init', noupdate=True)
        return True

    def generate_config_file(self, cr, uid, ids, context=None):
        object_obj = self.pool.get('import.data.run.object')

        for run in self.browse(cr, uid, ids, context):
            object_ids = [obj.id for obj in run.object_ids]
            config_path = run.config_path
            if not os.path.exists(config_path): os.makedirs(config_path)
            object_obj.generate_config_file(cr, uid, object_ids, config_path, context)
        return True

    def genertate_template_file(self, cr, uid, ids, context=None):
        object_obj = self.pool.get('import.data.run.object')

        for run in self.browse(cr, uid, ids, context):
            object_ids = [obj.id for obj in run.object_ids]
            object_obj.genertate_template_file(cr, uid, object_ids, context)
        return True

    def convert_file2csv(self, cr, uid, ids, context=None):
        file_obj = self.pool.get('import.data.run.object.file')

        for run in self.browse(cr, uid, ids, context):
            data2convert_path = run.run_data_path + '2convert/'
            save_folder_path = run.run_data_path + '2check/'
            file_paths = []
            for root, dirs, files in os.walk(data2convert_path):
                for i in files:
                    file_paths.append(os.path.join(root, i))

            if not os.path.exists(data2convert_path):
                raise orm.except_orm('Error', _(u"Le dossier %s n'existe pas. Merci de le créer et de mettre les fichiers à convertir") % (data2convert_path,))

            if not file_paths:
                raise orm.except_orm('Error', _(u"Aucun fichier n'a été trouvé à l'emplacementLe dossier %s. Merci d'y placer vos fichiers à convertir") % (data2convert_path,))

            for file_path in file_paths:
                file_obj.convert_file2csv(cr, uid, file_path, save_folder_path, context)

        return True

    def log(self, cr, uid, ids, description, level='error', context=None):
        if not isinstance(ids, list):
            ids = [ids]
        id_lod_obj = self.pool.get('import.data.log')
        for run in self.browse(cr, uid, ids, context):
            id_lod_obj.log(cr, uid, run.id,
                                    False,
                                    False,
                                    description,
                                    level,
                                    context)


class ImportDataRunObjectCategory(orm.Model):

    _name = 'import.data.run.object.category'

    _columns = {
            'name': fields.char('Name', size=128),
                }


class ImportDataRunObject(orm.Model):

    _name = 'import.data.run.object'

    _columns = {
            'sequence': fields.integer('Sequence'),
            'name': fields.char('Model name', size=256, required=True),
            'model_id': fields.many2one('ir.model', 'Model', required=True),
            'nb_imported_items': fields.integer('Nb. Imported items', readonly=True),
            'nb_2import_items': fields.integer('Nb. of items to import', readonly=True),
            'import_type': fields.selection(IMPORT_TYPES, "Import type", readonly=False, required=True,),
            'import_script_name': fields.char('Import script name path', size=256, required=False),
            'file_ids':fields.one2many('import.data.run.object.file', 'object_id', string='Files to import', ondelete='cascade'),
            # validation result:
            'validation_failed_ok': fields.boolean('Validation failed'),
            'file_missed_ok': fields.boolean('File missed'),
            'validation_succeed_ok': fields.boolean('Validation succeeded'),
            'validation_date': fields.datetime('Files validated the'),
            # Validation information
            'apply_generic_validation_ok': fields.boolean('Apply generic checks', help='Apply generic checks'),
            'check_key_ok': fields.boolean('Check keys duplication', help='Checks if there are not duplicated keys in the file'),
            'check_nb_columns_ok': fields.boolean('Check number of columns ', help='Checks if the number of columns of the header is the same on all lines of the files'),
            'validation_script_name': fields.char('Validation script name path', size=256, required=False),
            'validation_field_ids':fields.one2many('import.data.run.object.validation.field', 'object_id', 'Field validation', ondelete='cascade'),
            'run_id': fields.many2one('import.data.run', 'Run', required=True, ondelete='cascade'),
            'log_ids':fields.one2many('import.data.log', 'object_id', 'Object logs', ondelete='cascade'),
            'description':fields.text('Description'),
            'manage_manually_ok':fields.boolean('Manage manually'),
            # 'template_checked_ok':fields.boolean('Template checked OK'),
            'note': fields.text('Notes'),
            }

    _defaults = {
            'apply_generic_validation_ok':True,
            'check_key_ok':True,
            'check_nb_columns_ok':True,
        }

    _order = "sequence asc"

    def set_manage_manually_true(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'manage_manually_ok':True}, context)
        return True
    def set_manage_manually_false(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'manage_manually_ok':False}, context)
        return True

    def initialize_objects(self, cr, uid, ids, context):
        """
            Initialize object with :
                Default Fields2 validates
                Default Files of each object
        """
        field_validation_obj = self.pool.get('import.data.run.object.validation.field')
        file_obj = self.pool.get('import.data.run.object.file')

        # Unlink fields
        for obj in self.browse(cr, uid, ids, context):
            # for each object create field validations
            if obj.manage_manually_ok:
                continue
            for field in obj.validation_field_ids:
                field_validation_obj.unlink(cr, uid, field.id, context)
            for file_iter in obj.file_ids:
                file_obj.unlink(cr, uid, file_iter.id, context)
        # create field validation from fields of the model
        # TODO manage inherit object
        for obj in self.browse(cr, uid, ids, context):
            if obj.manage_manually_ok:
                continue
            model_obj = self.pool.get(obj.model_id.model)
            for field in obj.model_id.field_id:
                if not model_obj._columns.get(field.name):
                    print "The field %s you try to initialize doesn't exist" % (field.name,)
                    continue
                if type(model_obj._columns[field.name]) in FIELD2SKIP:
                    continue
                field_name = field.name
                field_type = model_obj._columns[field.name]._type
                target_file = ''
                if field_type == 'many2one':
                    field_name = field.name + '/id'
                    target_file = model_obj._columns[field.name]._obj + '.csv'
                description = field_validation_obj.get_field_description(cr, uid, model_obj, field.name, context)
                data = {'field_id':field.id,
                        'file_field_name':field_name,
                        'target_file': target_file,
                        'object_id':obj.id,
                        'required_ok': model_obj._columns[field.name].required,
                        'field_type':field_type,
                        'description': description,
                        }
                field_validation_obj.create(cr, uid, data, context)

            if not obj.file_ids:
                data = {'name':obj.model_id.model + '.csv',
                        'object_id':obj.id,
                        'sequence':0,
                        }
                file_obj.create(cr, uid, data, context)
                obj.model_id.model
        return True


    def genertate_template_file(self, cr, uid, ids, context):
        import pdb;pdb.set_trace()
        for obj in self.browse(cr, uid, ids, context):
            template_folder = obj.run_id.templates_path
            if not os.path.exists(template_folder): os.makedirs(template_folder)

            file_name = '%s%s_%s.csv' % (template_folder, obj.sequence, obj.model_id.model)

            field_names = ['id']
            descriptions = [_("Defines the key: String with alphanumeric char + '_'. One occurence of '.' is authoriorised")]
            common_field_names = ['ID']

            for field in obj.validation_field_ids:
                name2search = obj.model_id.model + ',' + field.field_id.name
                res_trans = self.pool.get('ir.translation')._get_source(cr, uid, name2search, 'field', context.get('lang', False) or 'en_US')
                field_names.append(field.file_field_name)
                common_field_names.append(res_trans)
                descriptions.append(field.description)
            with open(file_name, 'wb') as new_file:
                csv_file = csv.writer(new_file, field_names, delimiter=',', quotechar='"')
                csv_file.writerow(field_names)
                csv_file.writerow([s.encode("utf-8") for s in common_field_names])
                csv_file.writerow([s.encode("utf-8") for s in descriptions])

        return True

    def generate_yaml_record(self, cr, uid, obj_browse, context):

        # TODO method to improve
        field2export = [
            'sequence',
            'name',
            'import_type',
            'import_script_name',
            'apply_generic_validation_ok',
            'check_key_ok',
            'check_nb_columns_ok',
            'validation_script_name',
            'description',
            ]
        yaml = ''
        model_name = obj_browse._table._name
        record_id = model_name.replace('.', '_') + str(obj_browse.id)
        header = """-
  Create %s
-
  !record {model: %s, id:  %s}:
""" % (model_name, model_name, record_id)
        yaml += header
        ir_md = self.pool.get('ir.model.data')
        ident = '    '
        yaml += '%srun_id : %s\n' % (ident, obj_browse.run_id.ir_model_data_ref)
        yaml += '%smanage_manually_ok : %s\n' % (ident, obj_browse.manage_manually_ok and 'True' or 'False')
        imd_model_name = 'model_%s' % obj_browse.model_id.model.replace('.', '_')
        imd_id = ir_md.search(cr, uid, [('model', '=', 'ir.model'),
                                        ('name', '=', imd_model_name)],
                              order='id asc',
                              limit=1,
                              context=context)
        if imd_id:
            model_module = ir_md.browse(cr, uid, imd_id[0], context).module
        yaml += '%smodel_id : %s\n' % (ident, model_module + '.' + imd_model_name)
        for field in field2export:
            yaml += '%s%s : %s\n' % (ident, field, obj_browse[field])

        o2m1_ident = '      - '
        o2m2_ident = '        '

        if obj_browse.file_ids:
            yaml += '%sfile_ids :\n' % (ident,)
            for file_iter in obj_browse.file_ids:
                yaml += '%ssequence : %s\n' % (o2m1_ident, file_iter.sequence)
                yaml += '%sname : %s\n' % (o2m2_ident, file_iter.name)
                yaml += '%simport_once : %s\n' % (o2m2_ident, file_iter.import_once)
                yaml += '%simport_script_name : %s\n' % (o2m2_ident, file_iter.import_script_name)

        if obj_browse.validation_field_ids:
            yaml += '%svalidation_field_ids :\n' % (ident,)
            for field in obj_browse.validation_field_ids:
                imd_field_name = 'field_%s_%s' % (field.field_id.model_id.model.replace('.', '_'), field.field_id.name)
#                imd_field_ids = ir_md.search(cr, uid, [('name', '=', imd_field_name)], context=context, limit=1)
#                if imd_field_ids :
#                    model_module = ir_md.read(cr, uid, imd_field_ids[0], ['module'], context)['module']
                imd_field_name = '%s.%s' % (field.field_id.modules, imd_field_name)
                yaml += '%srequired_ok : %s\n' % (o2m1_ident, field.required_ok)
                yaml += '%sfield_type : %s\n' % (o2m2_ident, field.field_type)
                yaml += '%sfield_id : %s\n' % (o2m2_ident, imd_field_name)
                yaml += '%sfile_field_name : %s\n' % (o2m2_ident, field.file_field_name)
                yaml += '%starget_file : %s\n' % (o2m2_ident, field.target_file)
                yaml += '%spython_code : %s\n' % (o2m2_ident, field.python_code)
                text_indent = '         '
                if field.description:
                    description_list = field.description.split('\n')
                    description = ''
                    for line in description_list:
                        description += text_indent + line
                    yaml += '%sdescription : |\n%s\n' % (o2m2_ident, description)

        return yaml

    def generate_config_file(self, cr, uid, ids, config_folder, context):
        yml_text = ''
        for obj in self.browse(cr, uid, ids, context):
            yml_text += self.generate_yaml_record(cr, uid, obj, context)
        with open(config_folder + 'config%s.yml' % time.strftime("%Y_%m_%d_%H_%M"), 'wb') as new_file:
            new_file.write(yml_text)
        return True

    def generic_validation(self, cr, uid, ids, context=None):
        """
            Apply generic validation to ids objects:
                Check if number of columns defined on the header 
                is correct on all lines 
                Check that each key on file is defined once
            return True if the test is OK
            else False
                
        """
        if not isinstance(ids, list):
            ids = [ids]

        file_obj = self.pool.get('import.data.run.object.file')
        res = True
        for obj in self.browse(cr, uid, ids, context):
            file_ids = self.get_attended_file_ids(cr, uid, obj, context)
            if obj.check_nb_columns_ok:
                field_ids = [field.id for field in obj.validation_field_ids]
                res = file_obj.check_columns(cr, uid, file_ids, field_ids, context)
            if not res :
                break
            if obj.check_key_ok:
                res = file_obj.check_key_ok(cr, uid, file_ids, context)
            if not res :
                break

        return res

    def script_validation(self, cr, uid, ids, context=None):
        """
            run the script validation on each file of the object (ids)
        """
        if not isinstance(ids, list):
            ids = [ids]

        if not isinstance(ids, list):
            ids = [ids]

        file_obj = self.pool.get('import.data.run.object.file')
        res = True
        for obj in self.browse(cr, uid, ids, context):
            file_ids = [f.id for f in obj.file_ids]
            res = file_obj.script_validation(cr, uid, file_ids, obj.validation_script_name, context)
            if not res :
                break
        return res

    def get_attended_file_ids(self, cr, uid, obj, context=None):
        attended_file_ids = []
        for file_iter in obj.file_ids:
            file_path = obj.run_id.run_data_path + file_iter.name
            if os.path.exists(file_path) :
                attended_file_ids.append(file_iter.id)
        return attended_file_ids

    def check_file_attendance(self, cr, uid, ids, context=None, log=True):
        """
            Check if all files are present
            return attended files of objects ids
        """
        attended_file_ids = []
        if not isinstance(ids, list):
            ids = [ids]
        for obj in self.browse(cr, uid, ids, context):
            for file_iter in obj.file_ids:
                file_path = obj.run_id.run_data_path + file_iter.name
                if not os.path.exists(file_path) and log:
                    file_iter.log(_("Missing file"), 'warning', context=context)
                else:
                    attended_file_ids.append(file_iter.id)
        return attended_file_ids

    def check_field_validation(self, cr, uid, ids, context=None):

        file_obj = self.pool.get('import.data.run.object.file')

        if not isinstance(ids, list):
            ids = [ids]

        res = True
        for obj in self.browse(cr, uid, ids, context):
            file_ids = self.get_attended_file_ids(cr, uid, obj, context)
            field2check_ids = [field.id for field in obj.validation_field_ids]
            res = file_obj.check_field_validation(cr, uid, file_ids, field2check_ids, context)
            if not res:
                break

        return res

    def check_file_validation(self, cr, uid, ids, context=None):
        '''
            Start validation of all files specified on the object
        '''
        res = True
        if not isinstance(ids, list):
            ids = [ids]
        for obj in self.browse(cr, uid, ids, context):
            try :
                obj.write({'validation_date':time.strftime('%Y-%m-%d %H:%M'),
                           'validation_succeed_ok':False,
                           'file_missed_ok':False})
                if not obj.file_ids:
                    obj.log(_('No file is defined'), 'warning', context=context)
                    continue

                attended_file_ids = self.check_file_attendance(cr, uid, obj.id, context)
                if not attended_file_ids:
                    obj.write({'file_missed_ok':True})
                    continue
                if obj.apply_generic_validation_ok:
                    res = self.generic_validation(cr, uid, obj.id, context)
                if not res:
                    continue

                if obj.validation_field_ids:
                    res = self.check_field_validation(cr, uid, obj.id, context)

                if not res:
                    continue

                if obj.validation_script_name:
                    res = self.script_validation(cr, uid, obj.id, context)

                if not res:
                    continue
                obj.write({'validation_succeed_ok':True})
            except Exception, e:
                obj.log("Une erreur s'est produite en traitant le fichier: %s - %s" % (obj.name, e), 'error', context=context)
                continue

        return res


    def import_file(self, cr, uid, ids, context=None):
        '''
            Start import data of the objects 'ids'
        '''
        # Start  validation
        res = self.check_file_validation(cr, uid, ids, context)
        if not res :
            self.log(cr, uid, ids, 'File validation process failed', context=context)
            return False

        file_obj = self.pool.get('import.data.run.object.file')
        for obj in self.browse(cr, uid, ids, context):
            if obj.import_type == 'import_data':
                for f in obj.file_ids:
                    f.import_data_csv()
            elif obj.import_type == 'script':
                if not obj.import_script_name:
                    self.log(cr, uid, obj.id, 'Import script name required!', context=context)
                    return False
                if not hasattr(self, obj.import_script_name):
                    self.log(cr, uid, obj.id, 'script name %s not found!' % obj.import_script_name, context=context)
                    return False
                getattr(self, obj.import_script_name)(cr, uid, obj.id, context)
        return True

    def log(self, cr, uid, ids, description, level='error', context=None):
        if not isinstance(ids, list):
            ids = [ids]
        id_lod_obj = self.pool.get('import.data.log')
        for obj_iter in self.browse(cr, uid, ids, context):
            id_lod_obj.log(cr, uid, obj_iter.run_id.id,
                                    obj_iter.id,
                                    False,
                                    description,
                                    level,
                                    context)


class ImportDataRunObjectFile(orm.Model):

    _name = 'import.data.run.object.file'

    _columns = {
        # Import configuration
        'sequence': fields.integer('Sequence', required=True),
        'name': fields.char('File path/name', size=256, required=True),
        'import_once': fields.boolean('Import once'),
        'import_script_name': fields.char('Import script name path', size=256, required=False),
        'object_id': fields.many2one('import.data.run.object', 'Object', required=True, ondelete='cascade'),
        'delimiter': fields.char('File separator', size=1, required=True),
        # Import information
        'imported_ok': fields.boolean('Imported', readonly=True),
        'nb_2import_items': fields.integer('Nb. of items to import', readonly=True),
        'nb_imported_items': fields.integer('Nb. Imported items', readonly=True),
        'file_validated_ok': fields.boolean('Validated'),
        'import_date': fields.datetime('Import date', readonly=True),
        'file_extension': fields.selection(FILE_EXTENSIONS, 'File extension', required=True),
        'log_ids':fields.one2many('import.data.log', 'file_id', 'File logs', ondelete='cascade'),
    }

    _defaults = {'file_extension':'csv',
                 'import_once':True,
                 'delimiter': ',',
   }

    def import_data_csv(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        nb_2import_items = 0
        nb_imported_items = 0
        logs = []
        for filecsv in self.browse(cr, uid, ids, context):
            delimiter = str(filecsv.delimiter)
            fname = filecsv.name
            import_path = filecsv.object_id.run_id.run_data_path + fname
            if not os.path.exists(import_path):
                raise Exception("Import path '%s' does not exist" % (import_path,))

            with open(import_path, 'r') as f:
                csvcontent = f.read()
                module = filecsv.object_id.model_id.model
                nb_2import_items, nb_imported_items, logs = convert_csv_import(cr, module, fname, csvcontent, delimiter=delimiter, context=context)
            filecsv.object_id.write({'nb_2import_items': nb_2import_items, 'nb_imported_items': nb_imported_items})
            for log in logs:
                filecsv.log(log)
        return True

    def log(self, cr, uid, ids, description, level='error', context=None):
        if not isinstance(ids, list):
            ids = [ids]
        id_lod_obj = self.pool.get('import.data.log')
        for file_iter in self.browse(cr, uid, ids, context):
            id_lod_obj.log(cr, uid, file_iter.object_id.run_id.id,
                                    file_iter.object_id.id,
                                    file_iter.id,
                                    description,
                                    level,
                                    context)
        return True

    def convert_file2csv(self, cr, uid, file_path, tocheck_file_path, context):

        def _get_utf8_value(cell):
            str_cell = unicode(cell).encode('utf8')
            str_cell = str_cell.split(':')
            if str_cell[0] == 'text':
                if cell.ctype == 0:
                    return ''
                return str_cell[1][2:-1].decode('cp1252')
            else:
                return str_cell[1]

        res = True
        csv_file_name = file_path.split('/')[-1]
        csv_file_name = '.'.join(csv_file_name.split('.')[:-1]) + '.csv'
        book = xlrd.open_workbook(file_path)
        rows = []
        for sheet in book.sheets():
            print 'NB Rows:', sheet.nrows
            for i in range(sheet.nrows):
                cell_list = []
                for cell in sheet.row(i):
                    str_cell = _get_utf8_value(cell)
                    cell_list.append(str_cell)
                rows.append(cell_list)
        with open(tocheck_file_path + csv_file_name, 'wb') as csv_file:
            print "File creation OK"
            csv_writer = csv.writer(csv_file)
            for row in rows:
                csv_writer.writerow(row)

        return res

    def check_key_ok(self, cr, uid, file_ids, key='id', context=None):
        """
            Checks Key : for each file (ids) 
            checks if all caracters are  alphanumeric or '_'
            Checks key duplication of all file_ids
            
        """
        res = True
        duplicated_keys = []
        keys = []

        for file_iter in self.browse(cr, uid, file_ids, context):
            # Read file
            current_run = file_iter.object_id.run_id
            file_path = current_run.run_data_path + '/' + file_iter.name
            with open(file_path, 'rb') as csvfile :
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                header = spamreader.next()
                if not key in header:
                    continue
                key_index = header.index(key)
                regex = re.compile("([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$|[a-zA-Z0-9_]+$)")
                for row in spamreader:
                    row_key = row[key_index]
                    if not regex.match(row_key):
                        file_iter.log(_("The key format of %s does not match of the expected one") % (row_key,))
                        res = False
                    else:
                        if not row_key in keys:
                            keys.append(row_key)
                        else:
                            duplicated_keys.append(row_key)
        if duplicated_keys:
            file_iter.object_id.log(_("Their are %s duplicated keys: %s")
                                    % (len(duplicated_keys), str(duplicated_keys)))
            res = False

        return res

    def script_validation(self, cr, uid, ids, script_name, context=None):
        """
            run the script validation (script_name) on each file (ids)
            return False if the validation is not done
        """
        # TODO: Not yet implemented

        return True

    def check_columns(self, cr, uid, ids, field_ids, context=None):
        """
            Check if fields (fields) of each file in (ids)
            respect the format
        """
        field_obj = self.pool.get('import.data.run.object.validation.field')
        field_names = [field.file_field_name for field in field_obj.browse(cr, uid, field_ids, context)]
        res = True
        for file_iter in self.browse(cr, uid, ids, context):
            # Read file
            current_run = file_iter.object_id.run_id
            file_path = current_run.run_data_path + file_iter.name
            with open(file_path, 'rb') as csvfile :
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                header = spamreader.next()
                len_field_names = len(field_names)
                if 'id' in header and 'id' not in field_names:
                    len_field_names += 1
                if len(header) != len_field_names:
                    file_iter.log(_("The header is not complete"), 'error', context)
                    res = False
                for field in field_names:
                    if field not in  header:
                        file_iter.log(_("The field %s is expected please try to add it") % (field,), 'error', context)
                        res = False
        return res

    def check_field_validation(self, cr, uid, ids, field_ids, context=None):
        """
            Check if fields (field_ids) of each file in (ids)
            fit with the expected format
        """
        field_obj = self.pool.get('import.data.run.object.validation.field')
        field_map = {}
        for field in field_obj.browse(cr, uid, field_ids, context):
            field_map[field.file_field_name] = field
        res = True
        for file_iter in self.browse(cr, uid, ids, context):
            # Read file
            current_run = file_iter.object_id.run_id
            file_path = current_run.run_data_path + '/' + file_iter.name
            with open(file_path, 'rb') as csvfile :
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                header = spamreader.next()
                for row in spamreader:
                    position = 0
                    for field in header:
                        if field == 'id':
                            position += 1
                            continue
                        res = field_obj.validate_field_value(cr, uid,
                                                             file_iter,
                                                             field_map[field],
                                                             row[position],
                                                             context)
                        position += 1
                        if not res:
                            break
        return res


class ImportDataRunObjectValidationField(orm.Model):

    _name = 'import.data.run.object.validation.field'

    _columns = {
            'field_id': fields.many2one('ir.model.fields', 'Field validation rule', required=False),
            'required_ok': fields.boolean('Required'),
            'field_type': fields.char('Field type', size=128),
            'check_ok': fields.boolean('Check field'),
            'file_field_name': fields.char('File field name', size=256, required=True),
            'target_file': fields.char('Target file', size=256, required=False, help='Please insert path of the file defines the referenced object'),
            'python_code':fields.text('Python code'),
            'object_id': fields.many2one('import.data.run.object', 'Object', required=True, ondelete='cascade'),
            'description':fields.text('Description'),
    }

    def validate_field_value(self, cr, uid, file_obj, field_browse, value, context):
        res = True
        obj_model = self.pool.get(field_browse.field_id.model_id.model)
        # Split field_name to treate many2one field
        field_name = field_browse.file_field_name.split('/')
        if not field_name[0] in obj_model._columns:
            file_obj.log(_("""Le champ "%s" n'est pas définit dans l'objet""")
                             % (field_name,), 'warning')
            return res
        field = obj_model._columns[field_name[0]]

        if not value and field_browse.required_ok:
            file_obj.log(_("""Field validation error on "%s" column: the field is required, please set the right value """) % (field_name,))
            return False
        if not value:
            return res
#        if not field.check_ok:
#            return res
        if not field_browse.field_type:
            # When the type is not specified
            # The validation is bypassed
            return res
        if field_browse.field_type == 'boolean':
            # regex: ^(True|False)$
            if not isinstance(eval(value), bool):
                file_obj.log(_("""Field validation error on "%s" column: the value "%s" does not match with expected vlaues "True" or "False" """) % (field_name, value))
                res = False
        elif field._type == 'many2one':
            # regex:[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$
            regex = re.compile("[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$")
            if not regex.match(value):
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" of the many2one does not match with expected 
                                value "module_name.key" (authorized char are a=>z A=>Z 0=>9 and '_') """)
                             % (field_name, value,))
                res = False
        elif field._type == 'date':
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:  # To be compatible with the old version of this module
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" does not match with expected date format YYYY-MM-DD""")
                             % (field_name, value,))
                res = False

        elif field._type == 'datetime':
            try:
                datetime.strptime(value, '%Y-%m-%d %H:%M')
            except ValueError:  # To be compatible with the old version of this module
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" does not match with expected date format YYYY-MM-DD HH:MM""")
                             % (field_name, value,))
                res = False
        elif field._type == 'float':
            # [0-9]+\.[0-9]+
            regex = re.compile("[0-9]+\.[0-9]+")
            if not regex.match(value):
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" of the float does not match with expected 
                                format "XXX.XX" (X 0 ==>9 ) and X must appear once on each side at least""") % (field_name, value,))
                res = False
        elif field._type == 'selection':
            if isinstance(field.selection, list):
                selection = dict(field.selection)
            else:
                selection = dict(field.selection(self, cr, uid, context))
            if value not in selection.keys():
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" doesn't appear in authorized values %s""") %
                             (field_name, value, str(selection.keys())))
                res = False
        elif field._type == 'integer':
            regex = re.compile("[0-9]+\.[0-9]+")
            if not regex.match(value):
                file_obj.log(_("""Field validation error on "%s" column: The value "%s" of the integer does not match with expected 
                                format "XXX" (X 0 ==>9 ) and X must appear once  least""") % (field_name, value,))
                res = False
        elif field._type == 'char':
            if len(value) > field.size:
                file_obj.log(_("""Field validation error on "%s" column: the size of the value "%s" exceed the expected one %s""")
                             % (field_name, value, field.size))
                res = False
        elif field._type == 'text':
            res = True
        elif field._type == 'serialized':
            res = True
        else:
            file_obj.log(_("""Field validation warning on "%s" column: the expected value "%s" format is unknown""")
                             % (field_name, value))
            res = True
        return res

    def get_field_description(self, cr, uid, obj, field_name, context=None):
        description = ''
        field_p = obj._columns[field_name]
        res_trans = self.pool.get('ir.translation')._get_source(cr, uid, obj._name + ',' + field_name, 'field', context.get('lang', False) or 'en_US')
        required_info = field_p.required and _(u'Le champ est obligatoire') or _(u"Le champ n'est pas obligatoire")
        if field_p._type == 'boolean':
            description = _(u"""Champ booléen: Valeurs autorisées: "True" or "False". """)
        elif field_p._type == 'many2one':
            description = _(u"""Champ many2one: Valeurs autorisées: 'module_name.key' défini dans le fichier %s\n
Exemple: import_data.product1""" % (field_p._obj + '.csv'))
        elif field_p._type == 'date':
            description = _(u"""Champ date: Valeurs autorisées: AAAA-MM-DD Exemple: 2012-05-28""")
        elif field_p._type == 'datetime':
            description = _(u"""Champ Date et heure: Valeurs autorisées: AAAA-MM-DD HH:MM:SS Exemple: 2012-05-28 12:30:SS""")
        elif field_p._type == 'float':
            description = _(u"""Champ de type réel: Valeurs autorisées: XXXXX.DD Exemple: 125.01 Merci de noter que le sépérateur des décimales est  '.'""")
        elif field_p._type == 'selection':
            if isinstance(field_p.selection, list):
                selection = dict(field_p.selection)
            else:
                selection = dict(field_p.selection(self, cr, uid, context))

            description = _(u"""Champ sélection: Valeurs autorisées: %s \nLa correspondance des valeurs est \n%s""" % (str(selection.keys()), str(selection)))
        elif field_p._type == 'integer':
            description = _(u"""Entier: Valeurs autorisées: XXXXX Exemple: 125 Merci de noter que la valeur ne contient ni un '.' et ','""")
        elif field_p._type == 'char':
            description = _(u"""Char: Valeurs autorisées: Du text. La taille maximale autorisée est %s""" % (field_p.size,))
        elif field_p._type == 'text':
            description = _(u"""Text: Valeurs autorisées: Du text sans limite de taille""")
        else:
            description = _(u"Le champ est inconnu %s" % (field_p._type,))

        return res_trans + ':\n' + description + required_info


class ImportDataLog(orm.Model):

    _name = 'import.data.log'


    _columns = {
            'file_id': fields.many2one('import.data.run.object.file', 'Current File'),
            'object_id': fields.many2one('import.data.run.object', 'Current Object'),
            'run_id': fields.many2one('import.data.run', 'Current run', required=True),
            'name': fields.char('Description', size=256, required=True),
            'log_create_date': fields.datetime('Cretae date'),
            'log_uid': fields.many2one('res.users', 'User'),
            'level': fields.selection([('error', 'Error'),
                                       ('warning', 'Warning'),
                                       ('success', 'Success'),
                                       ('info', 'Info')], 'Level', required=True)
            }

    _order = 'log_create_date asc'

    def log(self, cr, uid, run_id, object_id, file_id, description, level='error', context=None):

        description_bis = ''
        run_obj = self.pool.get('import.data.run')
        object_obj = self.pool.get('import.data.run.object')
        file_obj = self.pool.get('import.data.run.object.file')

        if run_id:
            description_bis = '%s:' % run_obj.browse(cr, uid, run_id).name
        if object_id:
            description_bis = '%s - Object %s:' % (description_bis, object_obj.browse(cr, uid, object_id).name)
        if file_id:
            description_bis = '%s - File %s:' % (description_bis, file_obj.browse(cr, uid, file_id).name)

        if description:
            description = '%s : %s' % (description_bis, description)

        self.create(cr, uid, {'run_id':run_id,
                            'object_id':object_id,
                            'file_id':file_id,
                            'name':description,
                            'level':level,
                            'log_uid': uid,
                            'log_create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            }, context)
        return True
