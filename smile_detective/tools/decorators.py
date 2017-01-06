# -*- coding: utf-8 -*-

import cProfile as Profile
import pstats
import StringIO
import time

from openerp.tools.func import wraps

from .logger import Logger


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = Logger()
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
        logger = Logger()
        query_logging = logger.check()
        if query_logging:
            start = time.time()
        try:
            return func(self, query, *args, **kwargs)
        finally:
            if query_logging:
                delay = time.time() - start
                logger.log_db_stats(delay)
                if logger.check(log_sql=True):
                    logger.log_query(query, delay)
    return wrapper
