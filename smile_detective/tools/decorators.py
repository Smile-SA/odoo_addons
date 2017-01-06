# -*- coding: utf-8 -*-

import cProfile as Profile
import pstats
from StringIO import StringIO
import time

from openerp.addons.smile_detective.models.logging import PerfLogger
from openerp.tools.func import wraps


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = PerfLogger()
        profiling = logger.check(log_python=True)
        if profiling:
            profile = Profile.Profile()
            profile.enable()
        try:
            return func(*args, **kwargs)
        finally:
            if profiling:
                profile.disable()
                s = StringIO.StringIO()
                stats = pstats.Stats(profile, stream=s).sort_stats('cumulative')
                stats.print_stats()
                logger.log_profile(s.getvalue())
    return wrapper


def sql_analyse(func):
    @wraps(func)
    def wrapper(self, query, *args, **kwargs):
        logger = PerfLogger()
        query_logging = logger.check(log_sql=True)
        if query_logging:
            start = time.time()
        try:
            return func(self, query, *args, **kwargs)
        finally:
            if query_logging:
                delay = time.time() - start
                logger.log_query(query, delay)
    return wrapper
