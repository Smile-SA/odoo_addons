# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import csv
import os
from xml.dom.minidom import parseString
import shutil

from odoo import fields, models, _
from odoo.exceptions import ValidationError


PYTHON_HEADER = '''# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).'''


class ExportCustomisation(models.TransientModel):
    _name = 'export.customizations'
    _description = 'Export customizations'

    module_name = fields.Char(string="Module name", required=True)
    path = fields.Char(string="Path", required=True)

    def export_customizations(self):
        self.ensure_one()
        if not os.path.exists(self.path):
            raise ValidationError(_("This path does not exist!"))
        directory_name = os.path.join(self.path, self.module_name)
        self.create_module(directory_name)
        shutil.make_archive(directory_name, 'zip', self.path, self.module_name)
        shutil.rmtree(directory_name)

    def create_module(self, module_name):
        if os.path.exists(module_name):
            raise ValidationError(_("This file already exists!"))
        os.mkdir(module_name)
        os.chdir(module_name)
        os.mkdir('models')
        os.mkdir('views')
        os.mkdir('security')
        self.create_init_file(os)
        self.create_models(os, module_name)
        self.create_views(os, module_name)
        self.create_security_file(os, module_name)
        self.create_manifest_file(os, module_name)

    def create_init_file(self, os):
        os.mknod('__init__.py')
        with open("__init__.py", mode='a') as txt:
            txt.write(PYTHON_HEADER + "\n"*2 +
                      "from . import models" + "\n")

    def create_manifest_file(self, os, module_name):
        os.chdir(module_name)
        os.mknod('__manifest__.py')
        data_security = self.get_file_path(
            os.path.join(module_name, 'security'))
        data_views = self.get_file_path(
            os.path.join(module_name, 'views'), '_views.xml')
        data_menus = self.get_file_path(
            os.path.join(module_name, 'views'), '_menus.xml')
        data = data_security + data_views + data_menus
        with open("__manifest__.py", mode='a') as txt:
            txt.write(PYTHON_HEADER + "\n"*2 +
                      "{\n"
                      " 'name': \"%s\",\n"
                      " 'author': 'Smile S.A',\n"
                      " 'description': '',\n"
                      " 'category': 'Uncategorized',\n"
                      " 'version': '1.0',\n"
                      " 'website': 'https://www.smile.eu',\n"
                      " 'web': False,\n"
                      " 'sequence': 80,\n"
                      " 'summary': '',\n"
                      " 'depends': ['fidema_app'],\n"
                      " 'data': %s,\n"
                      " 'application': False,\n"
                      " 'auto_install': False,\n"
                      " 'installable': True,\n"
                      "}" % (self.module_name, data)
                      )

    def get_file_path(self, directory_path, suffix=None):
        if os.path.exists(directory_path):
            files = []
            for file_name in os.listdir(directory_path):
                if not suffix or (suffix and suffix in file_name):
                    files.append(os.path.join(
                        os.path.basename(directory_path), file_name))
            return files

    def get_data_for_security_file(self):
        customized_models = self.env['ir.model'].search([]).filtered(lambda mod: mod.model.startswith('x_'))
        access_rules_datas = [['id', 'name', 'model_id/id', 'group_id/id', 'perm_read', 'perm_write',
                               'perm_create', 'perm_unlink']]
        for model in customized_models:
            for rule in model.access_ids:
                group = rule.group_id and rule.group_id._get_external_ids()[rule.group_id.id][0] or False
                access_rules_datas.append([f"access_{model.model.replace('x_', '').replace('.', '_')}",
                                           model.model.replace('x_', ''),
                                           f"model_{model.model.replace('x_', '').replace('.', '_')}",
                                           group,
                                           int(rule.perm_read),
                                           int(rule.perm_write),
                                           int(rule.perm_create),
                                           int(rule.perm_unlink),
                                           ])
        return access_rules_datas

    def create_security_file(self, os, module_name):
        access_rules_data = self.get_data_for_security_file()
        os.chdir(os.path.join(module_name, 'security'))
        # create ir.model.access.csv file
        if len(access_rules_data) > 1:
            with open('ir.model.access.csv', 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(access_rules_data)

    def create_models(self, os, module_name):
        all_customized_models = self.env['ir.model.fields'].search([
            ('is_customized_field', '=', True),
        ]).filtered(
            lambda field: field.name.startswith('x_')).mapped('model_id')
        customized_models = self.env['ir.model'].search([]).filtered(lambda model: model.model.startswith('x_'))
        models_with_customized_fields = all_customized_models - customized_models
        os.chdir(os.path.join(module_name, 'models'))
        # Create init file
        os.mknod('__init__.py')
        with open("__init__.py", mode='a') as txt:
            txt.write(PYTHON_HEADER + "\n" * 2)
            for model in all_customized_models:
                txt.write(f"from . import {model.model.replace('x_', '').replace('.', '_')}\n")
        # Create customized models
        for model in customized_models:
            with open("%s.py" % model.model.replace('x_', '').replace('.', '_'), mode='w') as txt:
                txt.write(PYTHON_HEADER + "\n" * 2 +
                          "from odoo import fields, models" + "\n" * 3 +
                          "class %s(models.Model):" % model.name.title() + "\n" +
                          "    _name = '%s'" % model.model.replace('x_', '') + "\n" +
                          "    _description = '%s'" % model.name + "\n" * 2
                          )
                # Add fields
                for field in model.field_id.filtered(lambda field: field.name.startswith('x_')):
                    txt.write(f"    {self.get_field_declaration(field)}\n")

        # Inherit models and add customized fields
        for model in models_with_customized_fields:
            with open("%s.py" % model.model.replace('.', '_'), mode='w') as txt:
                txt.write(PYTHON_HEADER + "\n" * 2 +
                          "from odoo import fields, models" + "\n" * 3 +
                          "class %s(models.Model):" % model.name.title() + "\n" +
                          "    _inherit = '%s'" % model.model + 2 * "\n"
                          )
                # Add fields
                for field in model.field_id.filtered(
                        lambda field: field.is_customized_field and
                        field.name.startswith('x_')):
                    txt.write(f"    {self.get_field_declaration(field)}\n")

    def create_views(self, os, module_name):
        os.chdir(os.path.join(module_name, 'views'))
        # Create views custom
        customized_views = self.env['ir.ui.view'].search([
            '|',
            ('is_view_customize', '=', True),
            ('is_view_generated', '=', True),
        ], order='is_view_generated desc')
        files_views = {}
        for view in customized_views:
            view_name = view.model.replace('.', '_') + '_views'
            if view_name not in files_views:
                files_views[view_name] = ''
                files_views[view_name] += \
                    '<?xml version="1.0" encoding="utf-8"?><odoo>\n'
            if view.is_view_customize:
                view_xml_id = view.inherit_id.xml_id
                if not view_xml_id:
                    view_xml_id = '{}.{}'.format(
                        self.module_name,
                        view.inherit_id.name.replace('_generate', ''))
                files_views[view_name] += \
                    '<record id="%s" model="ir.ui.view">' % \
                    view.name.replace('_custom', '_inherited') + \
                    '<field name="name">%s</field>' % \
                    view.name.replace('_custom', '_inherited') + \
                    '<field name="model">%s</field>' % \
                    view.model + \
                    '<field name="inherit_id" ref="%s"/>' % \
                    view_xml_id + \
                    '<field name="priority">%s</field>' % \
                    view.priority + \
                    '<field name="arch" type="xml">' + \
                    view.arch_base.replace('<?xml version="1.0"?>', '').\
                    replace('<data>', '').replace('</data>', '').\
                    replace('name="x_', 'name="') + \
                    '</field></record>\n'
            if view.is_view_generated:
                files_views[view_name] += \
                    '<record id="%s" model="ir.ui.view">' % \
                    view.name.replace('_generate', '') + \
                    '<field name="name">%s</field>' % \
                    view.name.replace('_generate', '') + \
                    '<field name="model">%s</field>' % \
                    view.model + \
                    '<field name="priority">%s</field>' % \
                    view.priority + \
                    '<field name="arch" type="xml">%s</field>' \
                    % view.arch_base + \
                    '</record>\n'
        # Write & Close files view
        for view_name, value_file in files_views.items():
            value_file += '</odoo>'
            with open("%s.xml" % view_name, mode='a') as txt:
                txt.write(parseString(value_file).toprettyxml())
        # Create menus and actions
        customized_menus = self.env['ir.ui.menu'].search([
            ('is_customized_menu', '=', True)
        ])
        for menu in customized_menus:
            with open("%s_menus.xml" % menu.name.replace(' ', '_'),
                      mode='a') as txt:
                menu_action_view = \
                    self.create_menus(menu, os.path.basename(module_name))
                txt.write(parseString(
                    '<?xml version="1.0" encoding="utf-8"?><odoo>' +
                    menu_action_view + '</odoo>').toprettyxml())

    def create_menus(self, menu, module_name):
        action_view = ''
        menu_view = '<!-- %s menu -->' % menu.name +\
                    '<record model="ir.ui.menu" id="%s_menu">' % menu.name +\
                    '<field name="name">%s</field>' % menu.name
        if menu.sequence:
            menu_view += '<field name="sequence">%s</field>' % menu.sequence
        if menu.action:
            if menu.action._get_external_ids()[menu.action.id]:
                menu_view += '<field name="action" ref="%s"/>' % \
                                 menu.action._get_external_ids()[menu.action.id][0]
            else:
                menu_view += '<field name="action" ref="%s.%s_action"/>' % (module_name, menu.action.name)
                action_view += self.create_customized_actions(menu.action, module_name)
        if menu.parent_id:
            if menu.parent_id._get_external_ids()[menu.parent_id.id]:
                return action_view + menu_view + '<field name="parent_id" ref="%s"/></record>' % \
                             menu.parent_id._get_external_ids()[menu.parent_id.id][0]
            else:
                menu_view += '<field name="parent_id" ref="%s.%s_menu"/></record>' % (module_name, menu.parent_id.name)
                menu_view = self.create_menus(menu.parent_id, module_name) + menu_view
        return (action_view + menu_view + '</record>').replace('</record></record>', '</record>')

    def create_customized_actions(self, action, module_name):
        if action._name == 'ir.actions.act_window':
            return self.create_window_action(action)
        elif action._name == 'ir.actions.act_url':
            return self.create_url_action(action)
        elif action._name == 'ir.actions.act_server':
            return self.create_server_action(action, module_name)
        elif action._name == 'ir.actions.act_report':
            return self.create_report_action(action)
        elif action._name == 'ir.actions.act_client':
            return self.create_client_action(action)

    def create_server_action(self, action, module_name):
        customized_action = '<!-- %s action -->' % action.name + \
                            '<record model="ir.actions.act_server" id="%s_action">' % action.name + \
                            '<field name="name">%s</field>' % action.name + \
                            '<field name="state">%s</field>' % action.state
        if action.model_id._get_external_ids()[action.model_id.id]:
            customized_action += '<field name="model_id" ref="%s"/>' % \
                   action.model_id._get_external_ids()[action.model_id.id][0]
        else:
            customized_action += '<field name="model_id" ref="%s.model_%s"/>' % \
               (module_name, action.model_id.model.replace('x_', '').replace('.', '_'))
        if action.state == 'code':
            return customized_action + '<field name="code">%s</field></record>' % action.code
        elif action.state in ['object_create', 'object_write']:
            fields_lines = ''
            fields_lines_ids = []
            for field_line in action.fields_lines:
                fields_lines_ids.append(f"(4, ref('{module_name}.{field_line.col1.name.replace('x_', '')}"
                                        f"_fields_lines'))")
                fields_lines += '<record model="ir.server.object.lines" id="%s_fields_lines">' % \
                                field_line.col1.name.replace('x_', '') + \
                                '<field name="evaluation_type">%s</field>' % field_line.evaluation_type + \
                                '<field name="resource_ref">%s</field>' % field_line.resource_ref + \
                                '<field name="value">%s</field>' % field_line.value
                if field_line.col1._get_external_ids()[field_line.col1.id]:
                    fields_lines += '<field name="col1" ref="%s"/>' % \
                                    field_line.col1._get_external_ids()[field_line.col1.id][0]
                else:
                    fields_lines += '<field name="col1" ref="%s.field_%s__%s"/></record>' % \
                        (module_name, field_line.col1.model_id.model.replace('x_', '').replace('.', '_'),
                         field_line.col1.name.replace('x_', ''))
            if fields_lines_ids:
                customized_action += '<field name="fields_lines" eval="[%s]"/>' % ",".join(fields_lines_ids)
            if action.state == 'object_create':
                if action.crud_model_id._get_external_ids()[action.crud_model_id.id]:
                    return fields_lines + customized_action + '<field name="crud_model_id" ref="%s"/></record>' % \
                           action.crud_model_id._get_external_ids()[action.crud_model_id.id][0]
                return fields_lines + customized_action + '<field name="crud_model_id" ref="%s.model_%s"/></record>' % \
                    (module_name, action.crud_model_id.model.replace('x_', '').replace('.', '_'))
            return fields_lines + customized_action + '</record>'
        elif action.state == 'multi':
            child_ids = []
            for child in action.child_ids:
                if child._get_external_ids()[child.id]:
                    child_ids.append(f"(4, ref('{child._get_external_ids()[child.id][0]}'))")
                else:
                    child_ids.append(f"(4, ref('{module_name}.{child.name}_action'))")
            if child_ids:
                return customized_action + '<field name="child_ids" eval="[%s]"/></record>' % ",".join(child_ids)
            return customized_action + '</record>'
        elif action.state == 'email':
            if action.template_id._get_external_ids()[action.template_id.id]:
                return customized_action + '<field name="template_id" ref="%s"/></record>' % \
                       action.template_id._get_external_ids()[action.template_id.id][0]
            else:
                template_id = '<record model="mail.template" id="%s_mail_template">' % \
                               action.template_id.name + \
                              '<field name="name">%s</field>' % action.template_id.name + \
                              '<field name="subject">%s</field>' % action.template_id.subject + \
                              '<field name="body_html">%s</field>' % action.template_id.body_html + \
                              '<field name="email_from">%s</field>' % action.template_id.email_from + \
                              '<field name="use_default_to" eval="%s"/>' % action.template_id.use_default_to + \
                              '<field name="email_to">%s</field>' % action.template_id.email_to + \
                              '<field name="partner_to">%s</field>' % action.template_id.partner_to + \
                              '<field name="email_cc">%s</field>' % action.template_id.email_cc + \
                              '<field name="reply_to">%s</field>' % action.template_id.reply_to + \
                              '<field name="scheduled_date">%s</field>' % action.template_id.scheduled_date
                if action.model_id._get_external_ids()[action.model_id.id]:
                    template_id += '<field name="model_id" ref="%s"/></records>' % \
                                    action.template_id.model_id._get_external_ids()[action.template_id.model_id.id][0]
                else:
                    template_id += '<field name="model_id" ref="%s.model_%s"/></records>' % \
                                    (module_name, action.template_id.model_id.model.replace('x_', '').replace('.', '_'))
                return template_id + customized_action + \
                    '<field name="template_id" ref="%s.%s_mail_template"/></record>' % \
                    (module_name, action.template_id.name)
        elif action.state == 'followers':
            create_partners = ''
            partner_ids = []
            create_channels = ''
            channel_ids = []
            for partner in action.partner_ids:
                if partner._get_external_ids()[partner.id]:
                    partner_ids.append(f"(4, ref('{partner._get_external_ids()[partner.id][0]}'))")
                else:
                    partner_ids.append(f"(4, ref('{module_name}.{partner.name}_partner'))")
                    create_partners += '<record model="res.partner" id="%s_partner">' % partner.name + \
                                       '<field name="name">%s</field></record>' % partner.name
            for channel in action.channel_ids:
                if channel._get_external_ids()[channel.id]:
                    channel_ids.append(f"(4, ref('{channel._get_external_ids()[channel.id][0]}'))")
                else:
                    channel_ids.append(f"(4, ref('{module_name}.{channel.name}_partner'))")
                    create_channels += '<record model="mail.channel" id="%s_channel">' % channel.name + \
                                       '<field name="name">%s</field></record>' % channel.name
            if channel_ids:
                customized_action += '<field name="channel_ids" eval="[%s]"/></record>' % \
                                     ",".join(channel_ids)
            if partner_ids:
                customized_action += '<field name="partner_ids" eval="[%s]"/></record>' % \
                                     ",".join(partner_ids)
            else:
                customized_action += '</record>'
            return create_channels + create_partners + customized_action
        elif action.state == 'next_activity':
            create_users = ''
            customized_action += '<field name="activity_type_id" ref="%s"/>' % \
                                 action.activity_type_id._get_external_ids()[action.activity_type_id.id][0] + \
                                 '<field name="activity_user_type">%s</field>' % action.activity_user_type
            if action.activity_user_id._get_external_ids()[action.activity_user_id.id]:
                customized_action += '<field name="activity_user_id" ref="%s"/>' % \
                                     action.activity_user_id._get_external_ids()[action.activity_user_id.id][0]
            else:
                create_users += '<record model="res.users" id="%s_user">' % action.activity_user_id.name + \
                                '<field name="name">%s</field>' % action.activity_user_id.name + \
                                '<field name="login">%s</field></record>' % action.activity_user_id.login
                customized_action += '<field name="activity_user_id" ref="%s.%s_user"/>' % \
                                     (module_name, action.activity_user_id.name)
            return create_users + customized_action
        elif action.state == 'sms':
            create_sms_template = ''
            if action.sms_template_id._get_external_ids()[action.sms_template_id.id]:
                customized_action += '<field name="template_id" ref="%s"/></record>' % \
                       action.sms_template_id._get_external_ids()[action.sms_template_id.id][0]
            else:
                create_sms_template = '<record model="sms.template" id="%s_sms_template">' % \
                                       action.sms_template_id.name + \
                                      '<field name="name">%s</field>' % action.sms_template_id.name + \
                                      '<field name="model_id" ref="%s"/>' % \
                                       action.sms_template_id.model_id._get_external_ids()[
                                          action.sms_template_id.model_id.id][0] +\
                                      '<field name="body">%s</field></records>' % action.sms_template_id.body
                customized_action += '<field name="template_id" ref="%s.%s_sms_template"/></record>' % \
                                     (module_name, action.sms_template_id.name)
            return create_sms_template + customized_action

    def create_window_action(self, action):
        return '<!-- %s action -->' % action.name + \
               '<record model="ir.actions.act_window" id="%s_action">' % action.name + \
               '<field name="name">%s</field>' % action.name + \
               '<field name="res_model">%s</field>' % action.res_model.replace('x_', '') + \
               '<field name="view_mode">tree,form</field>' \
               '</record>'

    def create_url_action(self, action):
        return '<!-- %s action -->' % action.name + \
               '<record model="ir.actions.act_url" id="%s_action">' % action.name + \
               '<field name="name">%s</field>' % action.name + \
               '<field name="target">%s</field>' % action.target + \
               '<field name="url">%s</field>' % action.url + \
               '</record>'

    def create_report_action(self, action):
        return '<!-- %s action -->' % action.name + \
               '<record model="ir.actions.act_report" id="%s_action">' % action.name + \
               '<field name="name">%s</field>' % action.name + \
               '<field name="model">%s</field>' % action.model.replace('x_', '') + \
               '<field name="report_type">%s</field>' % action.report_type + \
               '<field name="report_name">%s</field>' % action.report_name + \
               '</record>'

    def create_client_action(self, action):
        return '<!-- %s action -->' % action.name + \
               '<record model="ir.actions.act_client" id="%s_action">' % action.name + \
               '<field name="name">%s</field>' % action.name + \
               '<field name="tag">%s</field>' % action.tag + \
               '</record>'

    def get_field_declaration(self, field):
        field_declaration = f"{field.name.replace('x_', '')} = fields.{field.ttype.capitalize()}" \
                            f"(string='{field.field_description}'"
        # Add options
        if field.required:
            field_declaration += ", required=True"
        if field.readonly:
            field_declaration += ", readonly=True"
        if field.store:
            field_declaration += ", store=True"
        if field.index:
            field_declaration += ", index=True"
        if not field.copy:
            field_declaration += ", copy=False"
        if field.ttype == 'many2many':
            field_declaration += ", comodel_name='%s'" % field.relation
            if field.relation_table:
                field_declaration += ", relation='%s'" % field.relation_table
            if field.column1:
                field_declaration += ", column1='%s'" % field.column1
            if field.column2:
                field_declaration += ", column2='%s'" % field.column2
            if field.domain != '[]':
                field_declaration += ", domain=%s" % field.domain
        elif field.ttype == 'many2one':
            field_declaration += ", comodel_name='%s'" % field.relation
            field_declaration += ", ondelete='%s'" % field.on_delete
            if field.domain != '[]':
                field_declaration += ", domain=%s" % field.domain
        elif field.ttype == 'one2many':
            field_declaration += ", comodel_name='%s'" % field.relation
            field_declaration += ", inverse_name='%s'" % field.relation_field.replace('x_', '')
            if field.domain != '[]':
                field_declaration += ", domain=%s" % field.domain
        elif field.ttype in ['selection', 'reference']:
            field_declaration += ", selection=%s" % [(sel.value, sel.name) for sel in field.selection_ids]
        elif field.related:
            field_declaration += ", related='%s'" % field.related.replace('x_', '')
        field_declaration += ")"
        return field_declaration
