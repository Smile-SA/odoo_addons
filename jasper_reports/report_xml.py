##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import csv
import copy
import base64
import report
import pooler
from osv import orm, osv, fields
import tools
import tempfile 
import codecs
import sql_db
import netsvc
import jasper_report
from tools.translate import _

class report_xml_file(osv.osv):
	_name = 'ir.actions.report.xml.file'
	_columns = {
		'file': fields.binary('File', required=True, filters="*.jrxml,*.properties,*.ttf", help=''),
		'filename': fields.char('File Name', size=256, required=False, help=''),
		'report_id': fields.many2one('ir.actions.report.xml', 'Report', required=True, ondelete='cascade', help=''),
		'default': fields.boolean('Default', help=''),
	}
	def create(self, cr, uid, vals, context=None):
		result = super(report_xml_file,self).create(cr, uid, vals, context)
		self.pool.get('ir.actions.report.xml').update(cr, uid, [vals['report_id']], context)
		return result

	def write(self, cr, uid, ids, vals, context=None):
		result = super(report_xml_file,self).write(cr, uid, ids, vals, context)
		for attachment in self.browse(cr, uid, ids, context):
			self.pool.get('ir.actions.report.xml').update(cr, uid, [attachment.report_id.id], context)
		return result

report_xml_file()

# Inherit ir.actions.report.xml and add an action to be able to store .jrxml and .properties
# files attached to the report so they can be used as reports in the application.
class report_xml(osv.osv):
	_name = 'ir.actions.report.xml'
	_inherit = 'ir.actions.report.xml'
	_columns = {
		'jasper_output': fields.selection([('html','HTML'),('csv','CSV'),('xls','XLS'),('rtf','RTF'),('odt','ODT'),('ods','ODS'),('txt','Text'),('pdf','PDF')], 'Jasper Output'),
		'jasper_file_ids': fields.one2many('ir.actions.report.xml.file', 'report_id', 'Files', help=''),
		'jasper_model_id': fields.many2one('ir.model', 'Model', help=''), # We use jas-er_model
		'jasper_report': fields.boolean('Is Jasper Report?', help=''),
	}
	_defaults = {
		'jasper_output': lambda self, cr, uid, context: context and context.get('jasper_report') and 'pdf' or False,
	}

	def create(self, cr, uid, vals, context=None):
		if context and context.get('jasper_report'):
			vals['model'] = self.pool.get('ir.model').browse(cr, uid, vals['jasper_model_id'], context).model
			vals['type'] = 'ir.actions.report.xml'
			vals['report_type'] = 'pdf'
			vals['jasper_report'] = True
		return super(report_xml,self).create(cr, uid, vals, context)

	def write(self, cr, uid, ids, vals, context=None):
		if context and context.get('jasper_report'):
			if 'jasper_model_id' in vals:
				vals['model'] = self.pool.get('ir.model').browse(cr, uid, vals['jasper_model_id'], context).model
			vals['type'] = 'ir.actions.report.xml'
			vals['report_type'] = 'pdf'
			vals['jasper_report'] = True
		return super(report_xml,self).write(cr, uid, ids, vals, context)

	def update(self, cr, uid, ids, context={}):
		for report in self.browse(cr, uid, ids):
			has_default = False
			# Browse attachments and store .jrxml and .properties into jasper_reports/custom_reports
			# directory. Also add or update ir.values data so they're shown on model views.
			#for attachment in self.pool.get('ir.attachment').browse( cr, uid, attachmentIds ):
			for attachment in report.jasper_file_ids:
				content = attachment.file
				fileName = attachment.filename
				if not fileName or not content:
					continue
				path = self.save_file( fileName, content )
				if '.jrxml' in fileName:
					if attachment.default:
						if has_default:
							raise osv.except_osv(_('Error'), _('There is more than one report marked as default'))
						has_default = True
						# Update path into report_rml field.
						self.write(cr, uid, [report.id], {
							'report_rml': path
						})
						valuesId = self.pool.get('ir.values').search(cr, uid, [('value','=','ir.actions.report.xml,%s'% report.id)])
						data = {
							'name': report.name,
							'model': report.model,
							'key': 'action',
							'object': True,
							'key2': 'client_print_multi',
							'value': 'ir.actions.report.xml,%s'% report.id
						}
						if not valuesId:
							valuesId = self.pool.get('ir.values').create(cr, uid, data, context=context)
						else:
							self.pool.get('ir.values').write(cr, uid, valuesId, data, context=context)
							valuesId = valuesId[0]

			if not has_default:
				raise osv.except_osv(_('Error'), _('No report has been marked as default.'))

			# Ensure the report is registered so it can be used immediately
			jasper_report.register_jasper_report( report.report_name, report.model )
		return True

	def save_file(self, name, value):
		path = os.path.abspath( os.path.dirname(__file__) )
		path += '/custom_reports/%s' % name
		f = open( path, 'wb+' )
		try:
			f.write( base64.decodestring( value ) )
		finally:
			f.close()
		path = 'jasper_reports/custom_reports/%s' % name
		return path

report_xml()
