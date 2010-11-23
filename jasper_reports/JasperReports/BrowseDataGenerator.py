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
from xml.dom.minidom import getDOMImplementation
import xml.dom.minidom
from osv import orm, osv, fields
import tempfile 
import codecs

from JasperReport import *
from AbstractDataGenerator import *

class BrowseDataGenerator(AbstractDataGenerator):
	def __init__(self, report, model, pool, cr, uid, ids, context):
		self.report = report
		self.model = model
		self.pool = pool
		self.cr = cr
		self.uid = uid
		self.ids = ids
		self.context = context
		self._languages = []
		self.imageFiles = {}
		self.temporaryFiles = []

	def languages(self):
		if self._languages:
			return self._languages
		ids = self.pool.get('res.lang').search(self.cr, self.uid, [('translatable','=','1')])
		self._languages = self.pool.get('res.lang').read(self.cr, self.uid, ids, ['code'] )
		self._languages = [x['code'] for x in self._languages]
		return self._languages

	def valueInAllLanguages(self, model, id, field):
		context = copy.copy(self.context)
		values = {}
		for language in self.languages():
			if language == 'en_US':
				context['lang'] = False
			else:
				context['lang'] = language
			value = model.read(self.cr, self.uid, [id], [field], context=context)
			values[ language ] = value[0][field] or ''

		result = []
		for key, value in values.iteritems():
			result.append( '%s~%s' % (key, value) )
		return '|'.join( result )

	def generateIds(self, record, relations, path, currentRecords):
		unrepeated = set( [field.partition('/')[0] for field in relations] )
		for relation in unrepeated:
			root = relation.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
			if root == 'Attachments':
				ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('res_model','=',record._table_name),('res_id','=',record.id)])
				value = self.pool.get('ir.attachment').browse(self.cr, self.uid, ids, self.context)
			elif root == 'User':
				value = self.pool.get('res.users').browse(self.cr, self.uid, [self.uid], self.context)
			else:
				if root == 'id':
					value = record._id
				elif record.__hasattr__(root):
					value = record.__getattr__(root)
				else:
					print "Field '%s' does not exist in model '%s'." % (root, record._table)
					continue

				if isinstance(value, orm.browse_record):
					relations2 = [ f.partition('/')[2] for f in relations if f.partition('/')[0] == root and f.partition('/')[2] ]
					return self.generateIds( value, relations2, currentPath, currentRecords )

				if not isinstance(value, list):
					print "Field '%s' in model '%s' is not a relation." % (root, self.model)
					return currentRecords

			# Only join if there are any records because it's a LEFT JOIN
			# If we wanted an INNER JOIN we wouldn't check for "value" and
			# return an empty currentRecords
			if value:
				# Only 
				newRecords = []
				for v in value:
					currentNewRecords = []
					for id in currentRecords:
						new = id.copy()
						new[currentPath] = v
						currentNewRecords.append( new )
					relations2 = [ f.partition('/')[2] for f in relations if f.partition('/')[0] == root and f.partition('/')[2] ]
					newRecords += self.generateIds( v, relations2, currentPath, currentNewRecords )

				currentRecords = newRecords
		return currentRecords
		
class XmlBrowseDataGenerator(BrowseDataGenerator):
	# XML file generation works as follows:
	# By default (if no OPENERP_RELATIONS property exists in the report) a record will be created
	# for each model id we've been asked to show. If there are any elements in the OPENERP_RELATIONS
	# list, they will imply a LEFT JOIN like behaviour on the rows to be shown.
	def generate(self, fileName):
		self.allRecords = []
		relations = self.report.relations()
		# The following loop generates one entry to allRecords list for each record
		# that will be created. If there are any relations it acts like a
		# LEFT JOIN against the main model/table.
		for record in self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context):
			newRecords = self.generateIds( record, relations, '', [ { 'root': record } ] )
			copies = 1
			if self.report.copiesField() and record.__hasattr__(self.report.copiesField()):
				copies = int( record.__getattr__(self.report.copiesField()) )
			for new in newRecords:
				for x in xrange(copies):
					self.allRecords.append( new )

		# Once all records have been calculated, create the XML structure itself
		self.document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = self.document.documentElement
		for records in self.allRecords:
			recordNode = self.document.createElement('record')
			topNode.appendChild( recordNode )
			self.generateXmlRecord( records['root'], records, recordNode, '', self.report.fields() )

		# Once created, the only missing step is to store the XML into a file
		f = codecs.open( fileName, 'wb+', 'utf-8' )
		try:
			topNode.writexml( f )
		finally:
			f.close()

	def generateXmlRecord(self, record, records, recordNode, path, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once by using a set.
		unrepeated = set( [field.partition('/')[0] for field in fields] )
		for field in unrepeated:
			root = field.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
			fieldNode = self.document.createElement( root )
			recordNode.appendChild( fieldNode )
			if root == 'Attachments':
				ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('res_model','=',record._table_name),('res_id','=',record.id)])
				value = self.pool.get('ir.attachment').browse(self.cr, self.uid, ids)
			elif root == 'User':
				value = self.pool.get('res.users').browse(self.cr, self.uid, self.uid, self.context)
			else:
				if root == 'id':
					value = record._id
				elif record.__hasattr__(root):
					value = record.__getattr__(root)
				else:
					value = None
					print "Field '%s' does not exist in model '%s'." % (root, record._table)

			# Check if it's a many2one
			if isinstance(value, orm.browse_record):
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generateXmlRecord(value, records, fieldNode, currentPath, fields2)
				continue

			# Check if it's a one2many or many2many
			if isinstance(value, orm.browse_record_list):
				if not value:
					continue
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if currentPath in records:
					self.generateXmlRecord(records[currentPath], records, fieldNode, currentPath, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generateXmlRecord(value[0], records, fieldNode, currentPath, fields2)
				continue

			# The rest of field types must be converted into str
			if field == 'id':
				# Check for field 'id' because we can't find it's type in _columns
				value = str(value)
			elif value == False:
				value = ''
			elif record._table._columns[field]._type == 'date':
				value = '%s 00:00:00' % str(value) 
			elif record._table._columns[field]._type == 'binary':
				imageId = (record.id, field)
				if imageId in self.imageFiles:
					fileName = self.imageFiles[ imageId ]
				else:
					fd, fileName = tempfile.mkstemp()
					try:
						os.write( fd, base64.decodestring( value ) )
					finally:
						os.close( fd )
					self.temporaryFiles.append( fileName )
					self.imageFiles[ imageId ] = fileName
				value = fileName
			elif isinstance(value, str):
				value = unicode(value, 'utf-8')
			elif not isinstance(value, unicode):
				value = unicode(value)

			valueNode = self.document.createTextNode( value )
			fieldNode.appendChild( valueNode )

class CsvBrowseDataGenerator(BrowseDataGenerator):
	# CSV file generation works as follows:
	# By default (if no OPENERP_RELATIONS property exists in the report) a record will be created
	# for each model id we've been asked to show. If there are any elements in the OPENERP_RELATIONS
	# list, they will imply a LEFT JOIN like behaviour on the rows to be shown.
	def generate(self, fileName):
		self.allRecords = []
		relations = self.report.relations()
		# The following loop generates one entry to allRecords list for each record
		# that will be created. If there are any relations it acts like a
		# LEFT JOIN against the main model/table.
		for record in self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context):
			newRecords = self.generateIds( record, relations, '', [ { 'root': record } ] )
			copies = 1
			if self.report.copiesField() and record.__hasattr__(self.report.copiesField()):
				copies = int( record.__getattr__(self.report.copiesField()) )
			for new in newRecords:
				for x in xrange(copies):
					self.allRecords.append( new )

		f = open( fileName, 'wb+' )
		try:
			csv.QUOTE_ALL = True
			# JasperReports CSV reader requires an extra colon at the end of the line.
			writer = csv.DictWriter( f, self.report.fieldNames() + [''], delimiter=",", quotechar='"' )
			header = {}
			for field in self.report.fieldNames() + ['']:
				if isinstance(field, unicode):
					name = field.encode('utf-8')
				else:
					name = field
				header[ field ] = name
			writer.writerow( header )
			# Once all records have been calculated, create the CSV structure itself
			for records in self.allRecords:
				row = {}
				self.generateCsvRecord( records['root'], records, row, '', self.report.fields() )
				writer.writerow( row )
		finally:
			f.close()

	def generateCsvRecord(self, record, records, row, path, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once by using a set.
		unrepeated = set( [field.partition('/')[0] for field in fields] )
		for field in unrepeated:
			root = field.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
			if root == 'Attachments':
				ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('res_model','=',record._table_name),('res_id','=',record.id)])
				value = self.pool.get('ir.attachment').browse(self.cr, self.uid, ids)
			elif root == 'User':
				value = self.pool.get('res.users').browse(self.cr, self.uid, self.uid, self.context)
			else:
				if root == 'id':
					value = record._id
				elif record.__hasattr__(root):
					value = record.__getattr__(root)
				else:
					value = None
					print "Field '%s' does not exist in model '%s'." % (root, record._table)


			# Check if it's a many2one
			if isinstance(value, orm.browse_record):
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generateCsvRecord(value, records, row, currentPath, fields2)
				continue

			# Check if it's a one2many or many2many
			if isinstance(value, orm.browse_record_list):
				if not value:
					continue
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if currentPath in records:
					self.generateCsvRecord(records[currentPath], records, row, currentPath, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generateCsvRecord(value[0], records, row, currentPath, fields2)
				continue

			# The field might not appear in the self.report.fields()
			# only when the field is a many2one but in this case it's null. This
			# will make the path to look like: "journal_id", when the field actually
			# in the report is "journal_id/name", for example.
			#
			# In order not to change the way we detect many2one fields, we simply check
			# that the field is in self.report.fields() and that's it.
			if not currentPath in self.report.fields():
				continue

			# Show all translations for a field
			type = self.report.fields()[currentPath]['type']
			if type == 'java.lang.Object':
				value = self.valueInAllLanguages(record._table, record.id, root)

			# The rest of field types must be converted into str
			if field == 'id':
				# Check for field 'id' because we can't find it's type in _columns
				value = str(value)
			elif value in (False,None):
				value = ''
			elif record._table._columns[field]._type == 'date':
				value = '%s 00:00:00' % str(value) 
			elif record._table._columns[field]._type == 'binary':
				imageId = (record.id, field)
				if imageId in self.imageFiles:
					fileName = self.imageFiles[ imageId ]
				else:
					fd, fileName = tempfile.mkstemp()
					try:
						os.write( fd, base64.decodestring( value ) )
					finally:
						os.close( fd )
					self.temporaryFiles.append( fileName )
					self.imageFiles[ imageId ] = fileName
				value = fileName
			elif isinstance(value, unicode):
				value = value.encode('utf-8')
			elif not isinstance(value, str):
				value = str(value)
			row[ self.report.fields()[currentPath]['name'] ] = value

