# (C) 2023 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.sql_db import Cursor

from ..tools import sql_analyse

Cursor.execute = sql_analyse(Cursor.execute)
