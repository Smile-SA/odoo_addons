# -*- coding: utf-8 -*-

import controllers
import models
import services
from tools import sql_analyse

from openerp.sql_db import Cursor

Cursor.execute = sql_analyse(Cursor.execute)
