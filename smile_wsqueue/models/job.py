# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime
from odoo import _, api, fields, models, registry
from odoo.api import Environment


LOGGER = logging.getLogger(__name__)


STATE_CANCELED = 'canceled'
STATE_DONE = 'done'
STATE_PENDING = 'pending'
STATE_ERROR = 'error'
STATE_IN_PROGRESS = 'in_progress'
LIST_STATE = [
    (STATE_PENDING, 'Pending'),
    (STATE_IN_PROGRESS, 'In progress'),
    (STATE_DONE, 'Done'),
    (STATE_ERROR, 'Error'),
    (STATE_CANCELED, 'Canceled')
]


def _write_and_commit(job, vals, cr):
    job.write(vals)
    cr.commit()


class Job(models.AbstractModel):
    _name = 'queue.job'
    _description = 'Queue job'
    _order = 'execute_date DESC, create_date DESC'

    method = fields.Selection([], 'Method')

    max_tries = fields.Integer('Max. tries', default=3)
    tries = fields.Integer('Tries', default=0, readonly=True, copy=False)
    total_tries = fields.Char('Total tries', compute='_get_total_tries')

    state = fields.Selection(LIST_STATE, 'State', default=STATE_PENDING,
                             readonly=True, copy=False)
    result = fields.Text('Result', readonly=True, copy=False)
    status_code = fields.Char('Status code', readonly=True, copy=False)

    execute_date = fields.Datetime('Execution date', readonly=True, copy=False)

    def call(self):
        logger = self._context.get('logger') or LOGGER
        # Sandbox a new environment
        with registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = Environment(new_cr, self.env.uid, self.env.context)
            new_self = self.with_env(new_env)

            # Iterate over pending jobs
            for job in new_self.sorted(key=lambda j: j.id):
                logger.info(_('Start job {} on #{}').format(job.method,
                                                            job.id))

                try:
                    # Register current try and set state to 'in progress'
                    method = getattr(job, job.method)
                    tries = job.tries + 1
                    job.write({
                        'state': STATE_IN_PROGRESS,
                        'tries': tries,
                        'execute_date': datetime.now()
                    })

                    # Time to execute
                    result, status_code = method()
                    # If all went well, just set the state to 'done' and
                    # store the result accordingly
                    job.write({
                        'state': STATE_DONE,
                        'result': result,
                        'status_code': status_code
                    })
                except Exception as e:
                    # If something went wrong, update the state to 'error'
                    # or 'canceled' depending on the number of attempts
                    logger.info(_('Error in {} on #{}: {}').format(
                        job.method, job.id, e.args
                    ))
                    job.write({
                        'state':
                            STATE_ERROR if tries < job.max_tries
                            else STATE_CANCELED,
                        'result': e.args
                    })
                    if tries >= job.max_tries:
                        job.send_job_failure_mail()
                finally:
                    logger.info(_('End {} on #{}').format(job.method,
                                                            job.id))

    def execute_call(self):
        logger = self._context.get('logger') or LOGGER
        logger.info(_('Start execute_call'))
        try:
            self.call()
        except Exception as e:
            logger.error(_('Error with execute_call: {}'.format(e.args)))
        finally:
            logger.info(_('End execute_call'))
        return True

    @api.model
    def execute_cron(self):
        # Should be implemented in inherited models
        raise NotImplementedError()

    @api.model
    def filter_jobs(self):
        return self.search(
            [('state', 'in', (STATE_PENDING, STATE_ERROR))],
            order='id asc'
        ).ids

    def _get_total_tries(self):
        for record in self:
            record.total_tries = '{}/{}'.format(record.tries, record.max_tries)

    def send_job_failure_mail(self):
        self.ensure_one()
        mail_template = self.get_job_failure_mail_template()
        if mail_template:
            mail_id = mail_template.send_mail(
                self.id, force_send=True, email_values={'auto_delete': False})
            return mail_id
        return False

    def get_job_failure_mail_template(self):
        """
        Method to override
        Returns the mail_template used to send a mail upon jb cancel or error
        """
        return False
