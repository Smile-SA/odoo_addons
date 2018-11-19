# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import cProfile as Profile
import pstats
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import time

from odoo.tools.func import wraps

from .logger import PerfLogger


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = PerfLogger()
        if logger.active and logger.log_python:
            profile = Profile.Profile()
            profile.enable()
        try:
            return func(*args, **kwargs)
        finally:
            if logger.active and logger.log_python:
                profile.disable()
                s = StringIO()
                stats = pstats.Stats(profile, stream=s). \
                    sort_stats('cumulative')
                stats.print_stats()
                logger.log_profile(s.getvalue())
    return wrapper


def sql_analyse(func):
    @wraps(func)
    def wrapper(self, query, params=None, log_exceptions=None):
        logger = PerfLogger()
        if logger.active:
            start = time.time()
        try:
            return func(self, query, params, log_exceptions)
        finally:
            if logger.active:
                duration = time.time() - start
                logger.log_db_stats(duration)
                if duration >= logger.sql_min_duration > 0:
                    logger.log_slow_query(query, duration)
                if logger.log_sql:
                    logger.log_query(query, duration)
    return wrapper
