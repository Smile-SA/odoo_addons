# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2022 Smile (<https://www.smile.eu>). All Rights Reserved
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

{
    "name": "Smile Isolation Level",
    "version": "14.0.1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'https://www.smile.eu',
    "description": """
This module adds a decorator to override method to change
postgresql isolation level

```
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from odoo.addons.smile_isolation_level.tools.misc import change_isolation_level

@api.model
@change_isolation_level(level=ISOLATION_LEVEL_READ_COMMITTED)
def my_function():
    ...

```
    """,
    "depends": [
        'base',
    ],
    "data": [
    ],
    "test": [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
