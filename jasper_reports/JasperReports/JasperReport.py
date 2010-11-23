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
from xml.dom.minidom import getDOMImplementation
from lxml import etree
import xml.dom.minidom
import re

dataSourceExpressionRegExp = re.compile( r"""\$P\{(\w+)\}""" )

class JasperReport:
	def __init__(self, fileName, pathPrefix=''):
		self._reportPath = fileName
		self._pathPrefix = pathPrefix.strip()
		if self._pathPrefix and self._pathPrefix[-1] != '/':
			self._pathPrefix += '/'

		self._language = 'SQL'
		self._relations = []
		self._fields = {}
		self._fieldNames = []
		self._subreports = []
		self._copiesField = False
		self.extractProperties()

	def language(self):
		return self._language

	def fields(self):
		return self._fields

	def fieldNames(self):
		return self._fieldNames

	def subreports(self):
		return self._subreports

	def relations(self):
		return self._relations

	def copiesField(self):
		return self._copiesField

	def subreportDirectory(self):
		return os.path.join( os.path.abspath(os.path.dirname( self._reportPath )), '' )

	def standardDirectory(self):
		return os.path.join( os.path.abspath(os.path.dirname(__file__)), '..', 'report', '' )
	
	def extractProperties(self):
		# The function will read all relevant information from the jrxml file
			
		doc = etree.parse( self._reportPath )

		# Define namespaces
		ns = 'http://jasperreports.sourceforge.net/jasperreports'
		nss = {'jr': ns}

		# Language
		
		# Not that if either queryString or language do not exist the default (from the constructor)
		# is SQL.
		langTags = doc.xpath( '/jr:jasperReport/jr:queryString', namespaces=nss )
		if langTags:
			if langTags[0].get('language'):
				self._language = langTags[0].get('language').lower()
		
		# Relations
		relationTags = doc.xpath( '/jr:jasperReport/jr:property[@name="OPENERP_RELATIONS"]', namespaces=nss )
		if relationTags and 'value' in relationTags[0].keys():
			# TODO: Make this secure.
			self._relations = eval( relationTags[0].get('value') )
			self._relations = [self._pathPrefix + x for x in self._relations]
		if not self._relations and self._pathPrefix:
			self._relations = [self._pathPrefix[:-1]]

		# Repeat field
		copiesFieldTags = doc.xpath( '/jr:jasperReport/jr:property[@name="OPENERP_COPIES_FIELD"]', namespaces=nss )
		if copiesFieldTags and 'value' in copiesFieldTags[0].keys():
			self._copiesField = self._pathPrefix + copiesFieldTags[0].get('value')

		# fields and fieldNames
		fields = {}
		fieldTags = doc.xpath( '/jr:jasperReport/jr:field', namespaces=nss )
		for tag in fieldTags:
			name = tag.get('name')
			type = tag.get('class')
			children = tag.getchildren()
			path = tag.findtext('{%s}fieldDescription' % ns, '')
			#print "D2: ", tag.find('fieldDescription').text
			# Make the path relative if it isn't already
			if path.startswith('/data/record/'):
				path = self._pathPrefix + path[13:]
			# Remove language specific data from the path so:
			# Empresa-partner_id/Nom-name becomes partner_id/name
			# We need to consider the fact that the name in user's language
			# might not exist, hence the easiest thing to do is split and [-1]
			newPath = []
			for x in path.split('/'):
				newPath.append( x.split('-')[-1] )
			path = '/'.join( newPath )
			self._fields[ path ] = {
				'name': name,
				'type': type,
			}
			self._fieldNames.append( name )

		# Subreports
		# Here we expect the following structure in the .jrxml file:
		#<subreport>
		#  <dataSourceExpression><![CDATA[$P{REPORT_DATA_SOURCE}]]></dataSourceExpression>
		#  <subreportExpression class="java.lang.String"><![CDATA[$P{STANDARD_DIR} + "report_header.jasper"]]></subreportExpression>
		#</subreport>
		subreportTags = doc.xpath( '//jr:subreport', namespaces=nss )
		for tag in subreportTags:
			dataSourceExpression = tag.findtext('{%s}dataSourceExpression' % ns, '')
			if not dataSourceExpression:
				continue
			dataSourceExpression = dataSourceExpression.strip()
			m = dataSourceExpressionRegExp.match( dataSourceExpression )
			if not m:
				continue
			dataSourceExpression = m.group(1)
			if dataSourceExpression == 'REPORT_DATA_SOURCE':
				continue

			subreportExpression = tag.findtext('{%s}subreportExpression' % ns, '')
			if not subreportExpression:
				continue
			subreportExpression = subreportExpression.strip()
			subreportExpression = subreportExpression.replace('$P{STANDARD_DIR}', '"%s"' % self.standardDirectory() )
			subreportExpression = subreportExpression.replace('$P{SUBREPORT_DIR}', '"%s"' % self.subreportDirectory() )
			try:
				# TODO: Make this secure
				subreportExpression = eval( subreportExpression )
			except:
				print "COULD NOT EVALUATE EXPRESSION: '%s'" % subreportExpression
				# If we're not able to evaluate the expression go to next subreport
				continue
			if subreportExpression.endswith('.jasper'):
				subreportExpression = subreportExpression[:-6] + 'jrxml'

			# Model
			model = ''
			modelTags = tag.xpath( '//jr:reportElement/jr:property[@name="OPENERP_MODEL"]', namespaces=nss )
			if modelTags and 'value' in modelTags[0].keys():
				model = modelTags[0].get('value')
			
			pathPrefix = ''
			pathPrefixTags = tag.xpath( '//jr:reportElement/jr:property[@name="OPENERP_PATH_PREFIX"]', namespaces=nss )
			if pathPrefixTags and 'value' in pathPrefixTags[0].keys():
				pathPrefix = pathPrefixTags[0].get('value')

			self._subreports.append({
				'parameter': dataSourceExpression,
				'filename': subreportExpression,
				'model': model,
				'pathPrefix': pathPrefix,
			})

