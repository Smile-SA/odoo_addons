# -*- coding: utf-8 -*-


from odoo import api, models, fields, _


class Blog(models.Model):
    _name = 'blog.blog'
    _description = 'Blogs'
    _inherit = 'blog.blog'

    security_type = fields.Selection((('public', 'Public'), ('private', 'Private')), 'Security type', required=True)
    group_ids = fields.Many2many('res.groups', string="Authorized Groups")

    @api.multi
    def all_tags(self, min_limit=1):
        user = self.env['res.users'].browse(self._uid)
        group_ids = [g.id for g in user.groups_id]
        req = """
            SELECT
                p.blog_id, count(*), r.blog_tag_id
            FROM
                blog_post_blog_tag_rel r
                    join blog_post p on r.blog_post_id=p.id
                    join blog_blog b on p.blog_id=b.id
            WHERE
                p.blog_id in %s AND
                (b.security_type = 'public' OR (b.security_type = 'private' AND b.id in (SELECT bg.blog_blog_id FROM blog_blog_res_groups_rel bg WHERE bg.res_groups_id IN %s ) ))

            GROUP BY
                p.blog_id,
                r.blog_tag_id
            ORDER BY
                count(*) DESC
        """
        self._cr.execute(req, [tuple(self._ids), tuple(group_ids)])
        tag_by_blog = {i: [] for i in self._ids}
        for blog_id, freq, tag_id in self._cr.fetchall():
            if freq >= min_limit:
                tag_by_blog[blog_id].append(tag_id)

        tag_obj = self.env['blog.tag']
        for blog_id in tag_by_blog:
            tag_by_blog[blog_id] = tag_obj.browse(tag_by_blog[blog_id])
        return tag_by_blog


class BlogPost(models.Model):
    _name = 'blog.post'
    _inherit = 'blog.post'

    security_type = fields.Selection((('public', 'Public'), ('private', 'Private')), 'Security type', required=True)
    group_ids = fields.Many2many('res.groups', string="Authorized Groups")
