# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from datetime import datetime

from openerp import models, api, fields
from openerp.osv import osv
from openerp.tools.translate import _


IMPLEMENTATION = [('standard', 'Standard'),
                  ('no_gap', 'No gap'),
                  ('pcount', 'PCount')]

TYPEVALS = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    implementation = fields.Selection(IMPLEMENTATION, required=True, default='standard',
                                      help="Two sequence object implementations are offered: Standard "
                                      "and 'No gap'. The later is slower than the former but forbids any"
                                      " gap in the sequence (while they are possible in the former).")

    @api.model
    def _interpolation_dict(self):
        """
        Override method =====> ADD Pcount, Pmonth, Pyear
        """
        res = super(IrSequence, self)._interpolation_dict()
        if 'period_id' in self._context and 'journal_id' in self._context:
            period = self._context['period_id']
            journal_id = self._context['journal_id']
            pyear = datetime.strptime(period.date_start, "%Y-%m-%d").year
            py = pyear % 100
            pmonth = datetime.strptime(period.date_start, "%Y-%m-%d").month
            if len(str(pmonth)) == 1:
                pmonth = '0'+str(pmonth)
            else:
                pmonth = str(pmonth)
            self._cr.execute("""SELECT COUNT(*)
                                FROM account_move
                                WHERE state = %s
                                AND journal_id = %s
                                AND period_id = %s""", ('posted', journal_id, period.id))
            pcount = int(self._cr.fetchall()[0][0]) + 1
            res.update({'pcount': '%04d' % pcount, 'pyear': str(pyear), 'py': str(py), 'pmonth': str(pmonth)})
        return res

    def _next(self, cr, uid, ids, context=None):
        """
        Override method =====> Avoid having number_next_actual on sequence
        """
        if not ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        sequences = self.read(cr, uid, ids, ['name', 'company_id', 'implementation', 'number_next', 'prefix', 'suffix', 'padding'])
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
            seq['number_next'] = cr.fetchone()
        else:
            cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            self.invalidate_cache(cr, uid, ['number_next'], [seq['id']], context=context)
        # Added by SMILE: Add (cr, uid, context) to method signature
        d = self._interpolation_dict(cr, uid, context)
        # END
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        # Added by SMILE: Avoid having number_next_actual on sequence
        if seq['implementation'] == 'pcount':
            return interpolated_prefix
        # END
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix
