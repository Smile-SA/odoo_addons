# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile. All Rights Reserved
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

import random

from openerp.widgets import TinyInputWidget, register_widget
from openobject.widgets import JSLink



class Matrix(TinyInputWidget):

    template = "/smile_matrix_widget/widgets/templates/matrix.mako"

    javascript = [
        JSLink("smile_matrix_widget", "javascript/matrix.js"),
        ]


    def __init__(self, name, model, view=None, domain=[], context={}, **kwargs):
        #attrs = kwargs.get('attrs', {})
        #xml_attrs   = isinstance(attrs,   (str, unicode)) and eval(attrs)   or attrs
        #xml_context = isinstance(context, (str, unicode)) and eval(context) or context
        super(Matrix, self).__init__(**kwargs)


register_widget(Matrix, ["matrix"])
