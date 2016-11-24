# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

from ..tools import cursor


class TestBuild(TransactionCase):

    def setUp(self):
        super(TestBuild, self).setUp()
        self.branch = self.env.ref('smile_ci.scm_repository_branch_smile_addons_90')
        pending_builds = self.branch.build_ids.filtered(lambda build: build.state == 'pending')
        if pending_builds:
            pending_builds.unlink()

    def test_010_create_build(self):
        """
            1. As continuous integration manager, I force build creation
            2. I check build is created in pending state
        """
        previous_builds = self.branch.build_ids
        self.branch.force_create_build()
        with cursor(self.cr.dbname, False) as new_cr:
            current_builds = self.branch.with_env(self.env(cr=new_cr)).build_ids
            new_build = current_builds - previous_builds
            self.assertTrue(bool(new_build), "Build not created")
            self.assertEqual(new_build.state, 'pending', "Build not pending")

    def test_020_scheduler(self):
        """
            1. As continuous integration manager, I trigger builds scheduler
            2. I check scheduler runned
        """
        Build = self.env['scm.repository.branch.build'].with_context(**{'docker-in-docker': True})
        self.assertTrue(bool(Build.scheduler()), "Scheduler failed")
        with cursor(self.cr.dbname, False) as new_cr:
            build = self.branch.with_env(self.env(cr=new_cr)).build_ids[0]
            self.assertEqual(build.state, 'testing', "Build not testing")
