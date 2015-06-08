# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from xlwt import Workbook, easyxf, Style


TITLE_STYLE = easyxf('font: bold on;')


class XlwtReport(object):

    def __init__(self, book=None):
        self.book = book or Workbook(encoding='utf-8')
        self.sheet = None
        self.current_row = 0
        self.current_col = 0

    def add_sheet(self, name):
        self.sheet = self.book.add_sheet(name)
        self.current_row = 0
        self.current_col = 0

    def write_section_title(self, title, row=None, col=None):
        row = row or self.current_row
        col = col or self.current_col
        self.sheet.write(row, col, title, TITLE_STYLE)
        self.sheet.row(row).set_style(TITLE_STYLE)
        self.current_row += 1

    def write_row(self, datas, row=None, col=0, style=Style.default_style):
        row = row or self.current_row
        for data in datas:
            self.sheet.write(row, col, data, style)
            col += 1
        self.current_row += 1

    def write_col(self, col, datas, row=0, style=Style.default_style):
        for data in datas:
            self.sheet.write(row, col, data, style)
            row += 1

    def write_merge(self, start_col, end_col, label, style=Style.default_style):
        self.sheet.write_merge(self.current_row, self.current_row, start_col, end_col, label, style)

    def add_blank_lines(self, line_count=1):
        self.current_row += line_count
