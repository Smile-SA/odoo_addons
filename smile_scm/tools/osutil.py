# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
from six import string_types
import subprocess
from subprocess import os
from threading import Lock

from odoo import _
from odoo.exceptions import UserError

_lock = Lock()
_logger = logging.getLogger(__name__)


@contextmanager
def cd(newPath):
    with _lock:
        newPath = newPath or '.'
        savedPath = None
        while not savedPath:
            try:
                savedPath = os.getcwd()
            except OSError:
                os.chdir("..")
        _logger.debug('Changing working directory to %s' % newPath)
        os.chdir(newPath)
        try:
            yield
        finally:
            _logger.debug('Changing working directory to %s' % savedPath)
            os.chdir(savedPath)


def check_output_chain(args, stdin=None, stdout=None, stderr=None):
    cmd = []
    for arg in args:
        if arg == '|':
            stdin = subprocess.Popen(
                cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr).stdout
            cmd = []
        else:
            cmd.append(arg)
    return subprocess.check_output(cmd, stdin=stdin, stderr=stderr)


def call(cmd, directory=None):
    if directory is None:
        return _call(cmd)
    with cd(directory):
        return _call(cmd)


def _call(cmd):
    command = cmd if isinstance(cmd, string_types) else ' '.join(cmd)
    _logger.debug('Calling command %s' % command)
    try:
        result = ''
        if isinstance(cmd, list):
            cmd = ' '.join(cmd)
        for operator in (' ; ', ' && ', ' || '):
            if isinstance(cmd, string_types):
                cmd = cmd.split(operator)
            else:
                cmd = sum([item.split(operator) for item in cmd], [])
        for subcmd in cmd:
            subresult = ''
            for subcmd2 in subcmd.split(' & '):
                subresult = check_output_chain(subcmd2.split(' '))
            result += subresult
        _logger.info('%s SUCCEEDED from %s' % (command, os.getcwd()))
        return result
    except subprocess.CalledProcessError as e:
        msg = _('%s FAILED\nfrom %s\n\n(#%s) %s') %  \
            (command, os.getcwd(), e.returncode, e.output)
        raise UserError(msg)
