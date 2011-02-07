# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

import mx.DateTime as dt




def compute_date(start_date, delta=0, uop='months',operation='add',format='%Y-%m-%d'):
    # delta = Nb of uop
    # operation 'add',minus
    
    if not start_date:
        return False
    
    if not delta:
        delta = 0
    
    new_date = False
    if operation == 'add':
        if uop=='months':
            new_date = dt.strptime(start_date,format)
            new_date += dt.RelativeDateTime(months=delta)
            #new_date -= dt.DateTimeDelta(1)
            new_date = new_date.Format(format)
    if operation == 'sub':
        if uop=='months':
            new_date = dt.strptime(start_date,format)
            new_date -= dt.RelativeDateTime(months=delta)
            #new_date += dt.DateTimeDelta(1)
            new_date = new_date.Format(format)
    
    return new_date
    