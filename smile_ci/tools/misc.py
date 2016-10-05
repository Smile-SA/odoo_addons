# -*- coding: utf-8 -*-

import unicodedata


def strip_accents(s):
    u = isinstance(s, unicode) and s or unicode(s, 'utf8')
    a = ''.join((c for c in unicodedata.normalize('NFKD', u) if unicodedata.category(c) != 'Mn'))
    return str(a)


def s2human(time):
    """Copy from https://github.com/odoo/odoo-extra/blob/master/runbot/runbot.py"""
    for delay, desc in [(86400, 'd'), (3600, 'h'), (60, 'm')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "s"
