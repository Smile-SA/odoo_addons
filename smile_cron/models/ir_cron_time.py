# -*- coding: utf-8 -*-

from openerp import api, models, fields

class IrCronTime(models.Model):
    _name = 'ir.cron.time'
    _rec_name = 'call_time'
    _order = 'cron_job_id, call_time asc'

    call_time = fields.Datetime('Next Execution Date', required=True,
                                help="Next planned execution date for this job.")
    cron_job_id = fields.Many2one('ir.cron', 'Cron job',
                                  required=True, ondelete='cascade')
