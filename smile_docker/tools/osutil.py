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
        os.chdir(newPath)
        try:
            yield
        finally:
            os.chdir(savedPath)


def check_output_chain(args, stdin=None, stdout=None, stderr=None):
    cmd = []
    for arg in args:
        if arg == '|':
            stdin = subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE,
                                     stderr=stderr).stdout
            cmd = []
        else:
            cmd.append(arg)
    return subprocess.check_output(cmd, stdin=stdin, stderr=stderr)


def call(cmd, directory=None):
    with cd(directory):
        command = cmd if isinstance(cmd, string_types) else ' '.join(cmd)
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
            raise UserError(_('%s FAILED\nfrom %s (return code: %s)\n\n%s')
                            % (command, os.getcwd(), e.returncode, e.output))
