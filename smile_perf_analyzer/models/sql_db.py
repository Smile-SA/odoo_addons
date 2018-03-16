# -*- coding: utf-8 -*-

from openerp.sql_db import Cursor

from ..tools import sql_analyse

Cursor.execute = sql_analyse(Cursor.execute)
