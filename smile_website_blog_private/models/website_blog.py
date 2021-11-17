# -*- coding: utf-8 -*-
# Copyright (C) 2022 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class Blog(models.Model):
    _inherit = 'blog.blog'

    security_type = fields.Selection(
        [('public', 'Public'), ('private', 'Private')],
        'Security type', required=True, default='public')
    group_ids = fields.Many2many('res.groups', string="Authorized Groups")

    def all_tags(self, join=False, min_limit=1):
        """ We have rewritten the native method
        to add the notion of group filtering

        :param min_limit:
        :return:
        """
        user = self.env['res.users'].browse(self._uid)
        group_ids = [g.id for g in user.groups_id]

        req = """
            SELECT p.blog_id,
                   count(*),
                   r.blog_tag_id
            FROM blog_post_blog_tag_rel r
            JOIN blog_post p ON r.blog_post_id=p.id
            JOIN blog_blog b ON p.blog_id=b.id
            WHERE p.blog_id IN %s
              AND (b.security_type = 'public'
                   OR (b.security_type = 'private'
                       AND b.id IN
                         (SELECT bg.blog_blog_id
                          FROM blog_blog_res_groups_rel bg
                          WHERE bg.res_groups_id IN %s )))
            GROUP BY p.blog_id,
                     r.blog_tag_id
            ORDER BY count(*) DESC
        """
        self._cr.execute(req, [tuple(self._ids), tuple(group_ids)])
        tag_by_blog = {i: [] for i in self._ids}
        all_tags = set()
        for blog_id, freq, tag_id in self._cr.fetchall():
            if freq >= min_limit:
                if join:
                    all_tags.add(tag_id)
                else:
                    tag_by_blog[blog_id].append(tag_id)

        tag_obj = self.env['blog.tag']

        if join:
            return tag_obj.browse(all_tags)

        for blog_id in tag_by_blog:
            tag_by_blog[blog_id] = tag_obj.browse(tag_by_blog[blog_id])
        return tag_by_blog


class BlogPost(models.Model):
    _inherit = 'blog.post'

    security_type = fields.Selection(
        [('public', 'Public'), ('private', 'Private')],
        'Security type', required=True, default='public')
    group_ids = fields.Many2many('res.groups', string="Authorized Groups")
