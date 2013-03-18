# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

import unicodedata


def strip_accents(msg):
    return ''.join((c for c in unicodedata.normalize('NFD', msg) if unicodedata.category(c) != 'Mn'))


def replace_non_ascii_by_space(msg):
    return "".join([ord(i) < 128 and i or ' ' for i in msg]).encode('ascii')


def clean_string(msg):
    return replace_non_ascii_by_space(strip_accents(unicode(msg)).upper())
