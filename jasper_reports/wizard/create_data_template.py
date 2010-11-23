# encoding: iso-8859-15
from xml.dom.minidom import getDOMImplementation
import wizard
import pooler
import base64
import osv
import string
from tools.translate import _

view_form_start = """<?xml version="1.0"?>
	<form string="Create Data Template">
		<group colspan="2">
			<field name="model"/>
			<field name="depth"/>
		</group>
	</form>"""

view_fields_start = {
	'model': { 'string': 'Model', 'type': 'many2one', 'relation': 'ir.model', 'required': True },
	'depth': { 'string':'Depth', 'type':'integer', 'required': True },
}

view_form_end = """<?xml version="1.0"?>
	<form string="Create Data Template">
		<group colspan="2">
			<field name="model"/>
			<field name="data" filename="filename"/>
			<field name="filename" invisible="1"/>
		</group>
	</form>"""

view_fields_end = {
	'model': { 'string': 'Model', 'type': 'char', 'readonly': True },
	'data': { 'string': 'XML', 'type': 'binary', 'relation': 'ir.model', 'readonly': True },
	'filename': { 'string': 'File Name', 'type': 'char' },
}

src_chars = """àáäâÀÁÄÂèéëêÈÉËÊìíïîÌÍÏÎòóöôÒÓÖÔùúüûÙÚÜÛçñºª·€ '"()/*-+?!&$[]{}@#`'^:;<>=~%\\""" 
src_chars = unicode( src_chars, 'iso-8859-1' )
dst_chars = """aaaaAAAAeeeeEEEEiiiiIIIIooooOOOOuuuuUUUUcnoa_e______________________________"""
dst_chars = unicode( dst_chars, 'iso-8859-1' )

class create_data_template(wizard.interface):
	
	def _action_start(self, cr, uid, data, context):
		res = {
			'depth': 1
		}
		return res

	def normalize(self, text):
		if isinstance( text, unicode ):
			text = text.encode('utf-8')
		return text

	def unaccent(self, text):
		if isinstance( text, str ):
			text = unicode( text, 'utf-8' )
		output = text
		for c in xrange(len(src_chars)):
			output = output.replace( src_chars[c], dst_chars[c] )
		return output.strip('_').encode( 'utf-8' )
		

	def generate_xml(self, cr, uid, context, pool, modelName, parentNode, document, depth, first_call):
		# First of all add "id" field
		fieldNode = document.createElement('id')
		parentNode.appendChild( fieldNode )
		valueNode = document.createTextNode( '1' )
		fieldNode.appendChild( valueNode )
		language = context.get('lang')
		if language == 'en_US':
			language = False

		# Then add all fields in alphabetical order
		model = pool.get(modelName)
		fields = model._columns.keys()
		fields.sort()
		for field in fields:
			name = False
			if language:
				# Obtain field string for user's language.
				name = pool.get('ir.translation')._get_source(cr, uid, modelName + ',' + field, 'field', language)
				#name = self.unaccent( name )
				#name = self.normalize( name )
				#help = pool.get('ir.translation')._get_source(cr, uid, modelName + ',' + field, 'help', language)
				#help = self.normalize( help )
			if not name:
				# If there's not description in user's language, use default (english) one.
				name = pool.get(modelName)._columns[field].string
				#help = pool.get(modelName)._columns[field].help

			if name:
				name = self.unaccent( name )
			# After unaccent the name might result in an empty string
			if name:
				name = '%s-%s' % (self.unaccent( name ), field )
			else:
				name = field
			fieldNode = document.createElement( name )
			#if name:
				#fieldNode.setAttribute( 'name', name )
			#if help:
				#fieldNode.setAttribute( 'help', help )

			parentNode.appendChild( fieldNode )
			fieldType = model._columns[field]._type
			if fieldType in ('many2one','one2many','many2many'):
				if depth <= 1:
					continue
				newName = model._columns[field]._obj
				self.generate_xml(cr, uid, context, pool, newName, fieldNode, document, depth-1, False)
				continue
			
			if fieldType == 'float':
				value = '12345.67'
			elif fieldType == 'integer':
				value = '12345'
			elif fieldType == 'date':
				value = '2009-12-31 00:00:00'
			elif fieldType == 'time':
				value = '12:34:56'
			elif fieldType == 'datetime':
				value = '2009-12-31 12:34:56'
			else:
				value = field

			valueNode = document.createTextNode( value )
			fieldNode.appendChild( valueNode )

		if depth > 1 and modelName != 'Attachments':
			# Create relation with attachments
			fieldNode = document.createElement( '%s-Attachments' % _('Attachments') )
			parentNode.appendChild( fieldNode )
			self.generate_xml(cr, uid, context, pool, 'ir.attachment', fieldNode, document, depth-1, False)

		if first_call:
			# Create relation with user
			fieldNode = document.createElement( '%s-User' % _('User') )
			parentNode.appendChild( fieldNode )
			self.generate_xml(cr, uid, context, pool, 'res.users', fieldNode, document, depth-1, False)
			

	def _action_create_xml(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		form = data['form']
		values = pool.get('ir.model').read(cr, uid, form['model'], ['name','model'], context)
		name = values['name']
		model = values['model']

		document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = document.documentElement
		recordNode = document.createElement('record')
		topNode.appendChild( recordNode )
		self.generate_xml( cr, uid, context, pool, model, recordNode, document, form['depth'], True )
		topNode.toxml()

		res = {
			'model': name,
			'data': base64.encodestring( topNode.toxml() ),
			'filename': 'jasper.xml',
		}
		return res

	states = {
		'init': {
			'actions': [_action_start],
			'result': {
				'type': 'form', 
				'arch': view_form_start, 
				'fields': view_fields_start, 
				'state': [('end','Cancel','gtk-cancel'),('create','Create','gtk-ok')]
			}
		},
		'create': {
			'actions': [_action_create_xml],
			'result': {
				'type': 'form', 
				'arch': view_form_end, 
				'fields': view_fields_end, 
				'state': [('end','Accept','gtk-ok')]
			}
		}
	}

create_data_template('jasper_create_data_template')
