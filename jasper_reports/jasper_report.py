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

from JasperReports import *

tools.config['jasperport'] = tools.config.get('jasperport', 8090)
tools.config['jasperpid'] = tools.config.get('jasperpid', False)

class Report:
	def __init__(self, name, cr, uid, ids, data, context):
		self.name = name
		self.cr = cr
		self.uid = uid
		self.ids = ids
		self.data = data
		self.model = self.data['model']
		self.context = context or {}
		self.pool = pooler.get_pool( self.cr.dbname )
		self.reportPath = None
		self.report = None
		self.temporaryFiles = []
		self.outputFormat = 'pdf'

	def execute(self):
		# Get the report path
		reports = self.pool.get( 'ir.actions.report.xml' )

		# Not only do we search the report by name but also ensure that 'report_rml' field
		# has the '.jrxml' postfix. This is needed because adding reports using the <report/>
		# tag, doesn't remove the old report record if the id already existed (ie. we're trying
		# to override the 'purchase.order' report in a new module). As the previous record is
		# not removed, we end up with two records named 'purchase.order' so we need to destinguish
		# between the two by searching '.jrxml' in report_rml.
		ids = reports.search(self.cr, self.uid, [('report_name', '=', self.name[7:]),('report_rml','ilike','.jrxml')], context=self.context)
		data = reports.read(self.cr, self.uid, ids[0], ['report_rml','jasper_output'])
		report = reports.browse(self.cr, self.uid, ids[0])

		import time

		# Check if attachment exits and return it
		objects = []
		if report.attachment:
			objects = self.pool.get(self.model).browse(self.cr, self.uid, self.ids)
			if report.attachment_use and len(self.ids) == 1:
				obj = objects[0]
				filename = eval(report.attachment, {'object': obj, 'time': time})
				if filename:
					attachment_ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('datas_fname', '=', filename+'.'+self.outputFormat),('res_model','=', self.model),('res_id','=', obj.id)])
					if attachment_ids:
						attachment = self.pool.get('ir.attachment').browse(self.cr, self.uid, attachment_ids[0])
						if attachment.datas:
							filecontent = base64.decodestring(attachment.datas)
							return (filecontent, self.outputFormat)

		if data['jasper_output']:
			self.outputFormat = data['jasper_output']
		self.reportPath = data['report_rml']
		self.reportPath = os.path.join( self.addonsPath(), self.reportPath )

		# Get report information from the jrxml file
		self.report = JasperReport( self.reportPath )

		# Create temporary input (XML) and output (PDF) files 
		fd, dataFile = tempfile.mkstemp()
		os.close(fd)
		fd, outputFile = tempfile.mkstemp()
		os.close(fd)
		self.temporaryFiles.append( dataFile )
		self.temporaryFiles.append( outputFile )

		start = time.time()

		# If the language used is xpath create the xmlFile in dataFile.
		if self.report.language() == 'xpath':
			if self.data.get('data_source','model') == 'records':
				#generator = XmlRecordDataGenerator()
				generator = CsvRecordDataGenerator()
			else:
				#generator = XmlBrowseDataGenerator( self.report, self.model, self.pool, self.cr, self.uid, self.ids, self.context )
				generator = CsvBrowseDataGenerator( self.report, self.model, self.pool, self.cr, self.uid, self.ids, self.context )
			generator.generate( dataFile )
			self.temporaryFiles += generator.temporaryFiles
		
		subreportDataFiles = []
		for subreportInfo in self.report.subreports():
			subreport = JasperReport( subreportInfo['filename'], subreportInfo ['pathPrefix'] )
			if subreport.language() == 'xpath':
				fd, subreportDataFile = tempfile.mkstemp()
				os.close(fd)
				subreportDataFiles.append({
					'parameter': subreportInfo['parameter'],
					'dataFile': subreportDataFile,
					'jrxmlFile': subreportInfo['filename'],
				})
				self.temporaryFiles.append( subreportDataFile )

				generator = CsvBrowseDataGenerator( subreport, self.model, self.pool, self.cr, self.uid, self.ids, self.context )
				generator.generate( subreportDataFile )
				

		# Call the external java application that will generate the PDF file in outputFile
		self.executeReport( dataFile, outputFile, subreportDataFiles )
		end = time.time()

		# Read data from the generated file and return it
		f = open( outputFile, 'rb')
		try:
			data = f.read()
		finally:
			f.close()

		# Remove all temporary files created during the report
		for file in self.temporaryFiles:
			try:
				os.unlink( file )
			except os.error, e:
				logger = netsvc.Logger()
				logger.notifyChannel("jasper_reports", netsvc.LOG_WARNING, "Could not remove file '%s'." % file )
		self.temporaryFiles = []
		
		# Create ir.attachment
		if report.attachment and len(self.ids) == 1:
			obj = objects[0]
			filename = eval(report.attachment, {'object': obj, 'time':time})
			if filename:
				attachment_ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('datas_fname', '=', filename+'.'+self.outputFormat),('res_model','=', self.model),('res_id','=', obj.id)])
				if attachment_ids:
					self.pool.get('ir.attachment').write(self.cr, self.uid, attachment_ids[0], {'datas': base64.encodestring(data)})
				else:
					self.pool.get('ir.attachment').create(self.cr, self.uid, {'name': filename,
																			  'datas': base64.encodestring(data),
																			  'datas_fname': filename + '.' + self.outputFormat,
																			  'res_model': self.model,
																			  'res_id': obj.id,
																			  }, context=self.context)
		return ( data, self.outputFormat )

	def path(self):
		return os.path.abspath(os.path.dirname(__file__))

	def addonsPath(self):
		return os.path.dirname( self.path() )

	def systemUserName(self):
		if os.name == 'nt':
			import win32api
			return win32api.GetUserName()
		else:
			import pwd
			return pwd.getpwuid(os.getuid())[0]

	def dsn(self):
		host = tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] or '5432'
		dbname = self.cr.dbname
		return 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )
	
	def userName(self):
		return tools.config['db_user'] or self.systemUserName()

	def password(self):
		return tools.config['db_password'] or ''

	def executeReport(self, dataFile, outputFile, subreportDataFiles):
		locale = self.context.get('lang', 'en_US')
		
		connectionParameters = {
			'output': self.outputFormat,
			#'xml': dataFile,
			'csv': dataFile,
			'dsn': self.dsn(),
			'user': self.userName(),
			'password': self.password(),
			'subreports': subreportDataFiles,
		}
		parameters = {
			'STANDARD_DIR': self.report.standardDirectory(),
			'REPORT_LOCALE': locale,
			'IDS': ','.join(map(str,self.ids)),
		}
		if 'parameters' in self.data:
			parameters.update( self.data['parameters'] )

		server = JasperServer( int( tools.config['jasperport'] ) )
		server.setPidFile( tools.config['jasperpid'] )
		server.execute( connectionParameters, self.reportPath, outputFile, parameters )


class report_jasper(report.interface.report_int):
	def __init__(self, name, model, parser=None ):
		# Remove report name from list of services if it already
		# exists to avoid report_int's assert. We want to keep the 
		# automatic registration at login, but at the same time we 
		# need modules to be able to use a parser for certain reports.
		if name in netsvc.SERVICES:
			del netsvc.SERVICES[name]
		super(report_jasper, self).__init__(name)
		self.model = model
		self.parser = parser

	def create(self, cr, uid, ids, data, context):
		name = self.name
		if self.parser:
			d = self.parser( cr, uid, ids, data, context )
			ids = d.get( 'ids', ids )
			name = d.get( 'name', self.name )
			# Use model defined in report_jasper definition. Necesary for menu entries.
			data['model'] = d.get( 'model', self.model )
			data['records'] = d.get( 'records', [] )
			# data_source can be 'model' or 'records' and lets parser to return
			# an empty 'records' parameter while still executing using 'records'
			data['data_source'] = d.get( 'data_source', 'model' )
			data['parameters'] = d.get( 'parameters', {} )
		r = Report( name, cr, uid, ids, data, context )
		#return ( r.execute(), 'pdf' )
		return r.execute()


# Ugly hack to avoid developers the need to register reports

import pooler
import report

def register_jasper_report(name, model):
	name = 'report.%s' % name
	# Register only if it didn't exist another "jasper_report" with the same name
	# given that developers might prefer/need to register the reports themselves.
	# For example, if they need their own parser.
	if netsvc.service_exist( name ):
		if isinstance( netsvc.SERVICES[name], report_jasper ):
			return
		del netsvc.SERVICES[name]
	report_jasper( name, model )


# This hack allows automatic registration of jrxml files without 
# the need for developers to register them programatically.

old_register_all = report.interface.register_all
def new_register_all(db):
	value = old_register_all(db)

	cr = db.cursor()
	# Originally we had auto=true in the SQL filter but we will register all reports.
	cr.execute("SELECT * FROM ir_act_report_xml WHERE report_rml ilike '%.jrxml' ORDER BY id")
	records = cr.dictfetchall()
	cr.close()
	for record in records:
		register_jasper_report( record['report_name'], record['model'] )
	return value

report.interface.register_all = new_register_all

