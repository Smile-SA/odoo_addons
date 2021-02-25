# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import registry
from odoo.tests.common import TransactionCase


class TestTalendJob(TransactionCase):

    def setUp(self):
        super(TestTalendJob, self).setUp()
        self.main_job = self.env.ref('smile_talend_job.main_job')
        self.main_job.child_ids.unlink()

    def test_010_talend_job_single(self):
        logs_nb = len(self.main_job.log_ids)
        self.main_job.with_context(in_new_thread=False).run()
        with registry(self.env.cr.dbname).cursor() as new_cr:
            self.assertEquals(len(self.main_job.with_env(
                self.env(cr=new_cr)).log_ids), logs_nb + 1)

    def test_020_talend_job_multiple(self):
        second_job = self.main_job.copy(
            default={'parent_id': self.main_job.id})
        second_job._cr.commit()
        self.assertEquals(len(second_job.log_ids), 0)
        self.main_job.with_context(in_new_thread=False).run_only()
        with registry(self.env.cr.dbname).cursor() as new_cr:
            self.assertEquals(len(second_job.with_env(
                self.env(cr=new_cr)).log_ids), 0)
        self.main_job.with_context(in_new_thread=False).run()
        with registry(self.env.cr.dbname).cursor() as new_cr:
            self.assertEquals(len(second_job.with_env(
                self.env(cr=new_cr)).log_ids), 1)

    def test_030_talend_job_context_propagation(self):
        second_job = self.main_job.copy(
            default={'parent_id': self.main_job.id})
        self.main_job.context = "Main context"
        self.assertFalse(second_job.context)
        self.main_job.propagate_context()
        self.assertEquals(second_job.context, self.main_job.context)
