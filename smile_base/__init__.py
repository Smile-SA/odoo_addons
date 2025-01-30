# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import controllers
from . import models
from . import tools
from . import wizard


def post_init_hook(env):
    add_act_window_id_in_context(env)
    set_default_lang(env)
    correct_datetime_format_fr(env)
    correct_datetime_format_eng(env)
    remove_menus(env)


def add_act_window_id_in_context(env):
    env['ir.actions.act_window'].with_context(
        active_test=False).search([])._update_context()


def set_default_lang(env):
    fr = env['res.lang'].with_context(active_test=False).search(
        [('code', '=', 'fr_FR')])
    wz = env['base.language.install'].create({'lang_ids': fr.ids})
    wz.lang_install()
    if fr:
        partner_lang_field_id = env.ref('base.field_res_partner__lang').id
        value = env['ir.default'].search(
            [('field_id', '=', partner_lang_field_id)], limit=1)
        vals = {
            'field_id': partner_lang_field_id,
            'json_value': '"fr_FR"',
        }
        if value:
            value.write(vals)
        else:
            value.create(vals)
    env.ref('base.user_root').lang = env.ref('base.lang_fr').code
    env.ref('base.user_admin').lang = env.ref('base.lang_fr').code


def correct_datetime_format_fr(env):
    language = env['res.lang'].search([('code', '=', 'fr_FR')], limit=1)
    if language:
        language.write({
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'grouping': '[3, 3, 3, 3, 3]',
            'decimal_point': ',',
            'thousands_sep': ' ',
        })


def correct_datetime_format_eng(env):
    language = env['res.lang'].search([('code', '=', 'en_US')], limit=1)
    if language:
        language.write({
            'date_format': '%m/%d/%Y',
            'time_format': '%H:%M:%S',
            'grouping': '[3, 3, 3, 3, 3]',
            'decimal_point': '.',
            'thousands_sep': ',',
        })


def remove_menus(env):
    for menu_id in ('base.module_mi', 'base.menu_module_updates'):
        try:
            env.ref(menu_id).unlink()
        except ValueError:
            pass
