"""Smile fabric decorators

.. module:: fabdecorator
   :platform: Debian or Ubuntu
   :synopsis: Helpers to build Smile fabric script

.. moduleauthor:: Corentin POUHET-BRUNERIE <corentin.pouhet-brunerie@smile.fr>
"""

from functools import wraps

from fabric.api import cd, env, lcd, settings

DEFAULTS = {
    'backup_dir': '/home/postgres',
    'sources_dir': '/opt/openerp',
}


def smile_path(dir, local=False):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not hasattr(env, dir):
                setattr(env, dir, DEFAULTS.get(dir, '/tmp'))
            if local:
                with lcd(getattr(env, dir)):
                    return func(*args, **kwargs)
            else:
                with cd(getattr(env, dir)):
                    return func(*args, **kwargs)
        return wrapper
    return wrap


def smile_secure(ok_ret_codes=[]):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            params = {'warn_only': not ok_ret_codes, 'ok_ret_codes': ok_ret_codes}
            with settings(**params):
                return func(*args, **kwargs)
        return wrapper
    return wrap


def smile_settings(host_type):
    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            setattr(env, host_type, {})
            for k, v in env.items():
                if k.startswith(host_type):
                    getattr(env, host_type)[k.replace('%s_' % host_type, '')] = v
            with settings(**getattr(env, host_type)):
                return func(*args, **kwargs)
        return wrapper
    return wrap
