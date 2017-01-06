# -*- coding: utf-8 -*-

import controllers
import models
import services
import tools import sql_analyse

import openerp.sql_db import Cursor

Cursor.execute = sql_analyse(Cursor.execute)
