# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, models, fields, _

class ResPartner(models.Model):

    _inherit = "res.partner"

    child_ids = fields.One2many('res.partner', 'parent_id','Contacts', domain=[('is_company', '=', False)])
    subsidiary_ids = fields.One2many('res.partner', 'parent_id','Subsidiaries', domain=[('is_company', '=', True)])
    partner_type = fields.Selection([('groupe','Groupe'),
                                     ('trade_name','Enseigne'),
                                     ('partner','Client'),
                                     ('store','Point de vente'),
                                     ('person','Contact'),
                                     ], required=True, default='partner')
    
    #TODO: Update tose fields in order to compute the value autoamtically
#     partner_groupe_id = fields.Many2one('res.partner',string='Groupe',compute='_update_hierarchy')
#     partner_enseigne_id = fields.Many2one('res.partner',string='Enseigne')
#     partner_client_id = fields.Many2one('res.partner',string='Client')
#     partner_point_vente_id = fields.Many2one('res.partner',string='Point de vente')


        
        
        