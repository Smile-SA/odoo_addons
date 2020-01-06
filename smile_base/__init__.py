# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import controllers
from . import models
from . import tools
from . import wizard

from odoo.api import Environment, SUPERUSER_ID
from odoo import tools


def pre_init_hook(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    fetchmail = env['ir.module.module'].search([
        ('name', '=', 'fetchmail'),
    ], limit=1)
    if fetchmail.state != 'installed':
        fetchmail.button_install()


def post_init_hook(cr, registry):
    add_act_window_id_in_context(cr)
    disable_update_notification_cron(cr)
    set_default_lang(cr)
    correct_datetime_format_fr(cr)
    correct_datetime_format_eng(cr)
    remove_menus(cr)


def add_act_window_id_in_context(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    env['ir.actions.act_window'].with_context(active_test=False).search([])._update_context()


def disable_update_notification_cron(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    cron = env.ref('mail.ir_cron_module_update_notification', False)
    if cron:
        cron.active = tools.config.get(
            'enable_publisher_warranty_contract_notification', False)


def set_default_lang(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    if env['res.lang'].search([('code', '=', 'fr_FR')], limit=1):
        partner_lang_field_id = env.ref('base.field_res_partner__lang').id
        value = env['ir.default'].search([('field_id', '=', partner_lang_field_id)], limit=1)
        vals = {
            'field_id': partner_lang_field_id,
            'json_value': '"fr_FR"',
        }
        if value:
            value.write(vals)
        else:
            value.create(vals)


def correct_datetime_format_fr(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    language = env['res.lang'].search([('code', '=', 'fr_FR')], limit=1)
    if language:
        language.write({
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'grouping': '[3, 3, 3, 3, 3]',
            'decimal_point': ',',
            'thousands_sep': ' ',
        })


def correct_datetime_format_eng(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    language = env['res.lang'].search([('code', '=', 'en_US')], limit=1)
    if language:
        language.write({
            'date_format': '%m/%d/%Y',
            'time_format': '%H:%M:%S',
            'grouping': '[3, 3, 3, 3, 3]',
            'decimal_point': '.',
            'thousands_sep': ',',
        })


def remove_menus(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    for menu_id in ('base.module_mi', 'base.menu_module_updates'):
        try:
            env.ref(menu_id).unlink()
        except ValueError:
            pass


