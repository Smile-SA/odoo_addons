# -*- coding: utf-8 -*-


def s2human(time):
    """
    Copy from https://github.com/odoo/odoo-extra/blob/master/runbot/runbot.py
    """
    for delay, desc in [(86400, 'd'), (3600, 'h'), (60, 'm')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "s"
