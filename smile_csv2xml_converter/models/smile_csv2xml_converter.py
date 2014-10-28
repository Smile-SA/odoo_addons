# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import csv
import base64

from openerp import models, fields, api

# import pdb;pdb.set_trace()


class SmileCsv2xmlConverter(models.Model):
    _name = "smile.csv2xml.converter"

    name = fields.Char("Name", required=True)
    object_id = fields.Many2one("ir.model", "Object", required=True)
    domain = fields.Char("Domain", default="[ ]", required=True)
    field_ids = fields.Many2many("ir.model.fields")
    model_xml = fields.Text("Modele XML", required=True, default=" a ")
    model_xml2 = fields.Text("Modele XML", required=True, default=" b ")
    xml_file = fields.Binary("xml file")
    file_origin = fields.Binary("file origin")

    csv_result = []

    @api.onchange('object_id')
    def onchange_object_id(self):
        field_ids = []
        if self.object_id:
            field_ids = self.env['ir.model.fields'].search([('model_id', '=', self.object_id.id)]).ids
            print field_ids
        self.field_ids = [[6, False, field_ids]]

    @api.multi
    def createXML(self):
        self.ensure_one()
        xml_fields = []
        object_field = {}
        decoded = base64.decodestring(self.file_origin)
        newcsv = open("newcsv.csv", "w+")
        newcsv.write(decoded)
        newcsv.close()
        csv_line = (csv.DictReader(open("newcsv.csv")))
        for field in self.field_ids:
            object_field.update({field.name: field.ttype})
            xml_fields.append(field.name)

        self.csv_result = self.get_xml_record(xml_fields, csv_line, object_field)

    @api.multi
    def fieldGeneration(self):
        self.ensure_one()
        model_xml = "<record id='##?##' model='##?##'>\n"
        for field in self.field_ids:
            if (field.ttype == "function" or field.ttype == "related" or field.name == "id"):
                model_xml += ""
            elif (field.ttype == "many2one"):
                model_xml += "        <field name='%s' ref='##?##'/>\n" % field.name
            elif (field.ttype == "many2many" or field.ttype == "one2many"):
                model_xml += "        <field name='%s' eval=\"##6##\"/>\n" % field.name
            else:
                model_xml += "        <field name='%s'>##?##</field>\n" % field.name
        model_xml += "</record>\n"
        self.model_xml = model_xml

    def get_xml_record(self, xml_fields, csv_line, object_field):
        modelsplit = self.model_xml.split('\n')
        xmlgenerated = "<?xml version='1.0' encoding='utf-8'?>\n"
        xmlgenerated += "<openerp>\n"
        xmlgenerated += "<data noupdate='1'>\n"
        # For each line in CSV file
        for dicline in csv_line:
            modelxml = self.model_xml
            xmlgenerated += "<record id='%s' model='%s'>\n" % (dicline['id'], self.object_id.model)
            # For each field (name) in the first tab
            for field in xml_fields:
                # Split the col with the index name given
                diclinesplitted = dicline[field].split(',')
                fieldname = "name='%s'" % field
                # For each line in model_xml
                for modelLine in modelsplit:
                    # Check if the field name is in the line
                    if fieldname in modelLine:
                        # If it is, do so
                        if (object_field[field] == "function" or object_field[field] == "related"):
                            xmlgenerated += ""
                        elif object_field[field] == "many2one":
                            modelxml = modelLine.replace("##?##", dicline[field], 1)
                        elif (object_field[field] == "many2many" or object_field[field] == "one2many"):
                            if "##6##" in modelLine:
                                tmp6 = "[(6,0,[ref('%s')" % diclinesplitted[0]
                                for i in range(1, len(diclinesplitted)):
                                    tmp6 += ",ref('%s')" % diclinesplitted[i]
                                tmp6 += "])]"
                                modelxml = modelLine.replace("##6##", tmp6, 1)
                            elif "##4##" in modelLine:
                                tmp4 = "[(4,ref('%s'))" % diclinesplitted[0]
                                for j in range(1, len(diclinesplitted)):
                                    tmp4 += ",(4,ref('%s'))" % diclinesplitted[j]
                                tmp4 += "]"
                                modelxml = modelLine.replace("##4##", tmp4, 1)
                        else:
                            modelxml = modelLine.replace("##?##", dicline[field], 1)
                        xmlgenerated += modelxml
                        xmlgenerated += "\n"
            xmlgenerated += "</record>\n"
        xmlgenerated += "</data>\n"
        xmlgenerated += "</openerp>"
        self.model_xml2 = xmlgenerated
        self.xml_file = base64.encodestring(self.model_xml2)
