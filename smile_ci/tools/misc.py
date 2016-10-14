# -*- coding: utf-8 -*-

import unicodedata


def strip_accents(s):
    u = isinstance(s, unicode) and s or unicode(s, 'utf8')
    a = ''.join((c for c in unicodedata.normalize('NFKD', u) if unicodedata.category(c) != 'Mn'))
    return str(a)


def s2human(time, details=False):
    for delay, desc in [(86400, 'd'), (3600, 'h'), (60, 'm')]:
        if time >= delay:
            result = str(int(time / delay)) + desc
            if details and desc == 'h':
                delta = time - int(time / delay) * delay
                result += str(int(delta / 60)).zfill(2)
            return result
    return str(int(time)) + "s"


def b2human(time):
    for delay, desc in [(1024**3, 'GiB'), (1024**2, 'MiB'), (1024, 'KiB')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "B"
