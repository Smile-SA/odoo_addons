# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        views = super(IrUiView, self).search(args, offset, limit, order)
        views = views.filter_visible_pages()
        return len(views) if count else views

    @api.multi
    @api.returns('self')
    def filter_visible_pages(self):
        def url(page):
            return page.key.replace('website.', '/page/')

        pages = self.filtered(lambda view: view.page_ids)
        if pages:
            urls = [url(page) for page in pages]
            context = {'website.menu.full_list': True}
            menus = self.env['website.menu'].with_context(
                **context).search([('url', 'in', urls)])
            visible_menus = menus.filter_visible_menus()
            not_visible_pages = pages.filtered(
                lambda page: url(page) in menus.mapped('url') and
                url(page) not in visible_menus.mapped('url'))
            return self - not_visible_pages
        return self
