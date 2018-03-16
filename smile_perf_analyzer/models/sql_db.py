# -*- coding: utf-8 -*-

from odoo.sql_db import Cursor

from ..tools import sql_analyse

Cursor.execute = sql_analyse(Cursor.execute)
