# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class StockPickingWaveType(models.Model):
    _name = 'stock.picking.wave.type'
    _description = 'Picking Wave Type'

    @api.model
    def _get_default_warehouse(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)

    name = fields.Char(required=True)
    code = fields.Selection([
        ('incoming', 'Suppliers'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')
    ], 'Type of Operation', required=True)
    active = fields.Boolean(default=True)
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence')
    partner_visible = fields.Boolean('Partner visible in wave', default=False)
    propagate_wave_cancel = fields.Boolean('Propagate wave cancellation', default=True,
                                           help='If checked, when wave is cancelled, picking lists are cancelled in cascade')
    propagate_picking_cancel = fields.Boolean('Propagate picking list cancellation', default=False,
                                              help='If checked, when picking list is cancelled, picking wave is cancelled in cascade')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', ondelete='cascade', default=_get_default_warehouse)


class StockPickingWave(models.Model):
    _name = 'stock.picking.wave'
    _inherit = ['stock.picking.wave', 'mail.thread']
    _description = 'Picking Wave'

    @api.model
    def _get_default_type(self):
        return self.env['stock.picking.wave.type'].search([], limit=1)

    type_id = fields.Many2one('stock.picking.wave.type', 'Type', readonly=True, states={'draft': [('readonly', False)]},
                              default=_get_default_type)
    partner_id = fields.Many2one('res.partner', 'Transport Company', domain=[('carrier', '=', True)],
                                 readonly=True, states={'draft': [('readonly', False)]})
    partner_visible = fields.Boolean('Partner visible', related="type_id.partner_visible", readonly=True)

    @api.one
    @api.constrains('type_id', 'picking_ids')
    def _check_picking_types(self):
        if self.picking_ids.filtered(lambda p: p.picking_type_id.code != self.type_id.code):
            raise Warning(_('You cannot link picking lists with a type of operations different from the wave'))

    @api.model
    def create(self, vals):
        type_id = vals.get('type_id') or self.default_get(['type_id'])['type_id']
        if type_id:
            wave_type = self.env['stock.picking.wave.type'].browse(type_id)
            if wave_type.sequence_id:
                vals['name'] = self.env['ir.sequence'].next_by_id(wave_type.sequence_id.id)
        return super(StockPickingWave, self).create(vals)

    @api.multi
    def cancel_picking(self):
        # Propagate cancellation to pickings if this is configured
        if not self:
            return True
        self = self.filtered(lambda wave: wave.state != 'cancel')
        waves_wo_propagation = self.filtered(lambda wave: wave.type_id and not wave.type_id.propagate_wave_cancel)
        waves_wo_propagation.mapped('picking_ids').write({'wave_id': False})
        return super(StockPickingWave, self).cancel_picking()


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    propagate_move_cancel = fields.Boolean('Propagate stock move cancellation', default=True,
                                           help='If checked, when stock move is cancelled, picking list is cancelled in cascade')
    propagate_picking_cancel = fields.Boolean('Propagate picking list cancellation', default=False,
                                              help='If checked, when picking list is cancelled, stock move is cancelled in cascade')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_cancel(self):
        if not self:
            return True
        self = self.filtered(lambda picking: picking.state != 'cancel')
        # Propagate cancellation to picking wave if this is configured
        waves_to_cancel = self.env['stock.picking.wave'].browse()
        for picking in self:
            if picking.wave_id.type_id.propagate_picking_cancel:
                waves_to_cancel |= picking.wave_id
        pickings_wo_propagation = self.filtered(lambda picking: picking.picking_type_id and not picking.picking_type_id.propagate_picking_cancel)
        moves = self.env['stock.move'].browse()
        for picking in pickings_wo_propagation:
            moves |= picking.move_lines
        moves.write({'picking_id': False})
        res = super(StockPicking, self).action_cancel()
        if self:
            # INFO: Because StockPicking.state is a function field without an inverse method
            self._cr.execute("UPDATE stock_picking SET state = 'cancel' WHERE id IN %s", (tuple(self.ids),))
        for picking in self:
            # Cancel waves whom all pickings are cancelled
            if not picking.wave_id.picking_ids.filtered(lambda picking: picking.state != 'cancel'):
                waves_to_cancel |= picking.wave_id
        waves_to_cancel.cancel_picking()  # Cancel picking waves
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_cancel(self):
        # Propagate cancellation to picking lists if this is configured
        if not self:
            return True
        self = self.filtered(lambda move: move.state != 'cancel')
        pickings = self.env['stock.picking'].browse()
        moves_to_unlink = self.browse()
        for move in self:
            if move.picking_id.picking_type_id.propagate_move_cancel:
                pickings |= move.picking_id
            else:
                moves_to_unlink |= move
        res = super(StockMove, self).action_cancel()
        pickings.action_cancel()
        moves_to_unlink.write({'picking_id': False})
        return res
