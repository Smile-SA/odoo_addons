# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

        pages = self.filtered(lambda view: view.page)
        if pages:
            urls = [url(page) for page in pages]
            context = {'website.menu.full_list': True}
            menus = self.env['website.menu'].with_context(**context).search([('url', 'in', urls)])
            visible_menus = menus.filter_visible_menus()
            not_visible_pages = pages.filtered(
                lambda page: url(page) in menus.mapped('url') and
                url(page) not in visible_menus.mapped('url'))
            return self - not_visible_pages
        return self
