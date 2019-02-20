# -*- coding: utf-8 -*-

from odoo import fields, models, _


class DockerLink(models.Model):
    _inherit = "docker.link"

    branch_id = fields.Many2one(
        "scm.repository.branch", "Branch", ondelete="cascade")

    _sql_constraints = [
        (
            "check_link",
            "CHECK(base_image_id IS NOT NULL OR branch_id IS NOT NULL)",
            _("Please specify a base image or a branch"),
        )
    ]
