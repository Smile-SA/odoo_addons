# -*- coding: utf-8 -*-

import os
from pexpect import spawn
from subprocess import check_call
import tempfile
import time


class AnsibleVault():

    def __init__(self, password=None, passfile=None):
        if (not password and not passfile) or (password and passfile):
            raise ValueError('Please specify a password or a passfile')
        if password and not isinstance(password, basestring):
            raise ValueError('password must be a string')
        if passfile and not os.path.isfile(passfile):
            raise ValueError('passfile must be a filepath')
        self._password = password
        self._passfile = passfile

    def encrypt_string(self, secret):
        return self._execute('encrypt', secret)

    def decrypt_string(self, secret, secretfile=None):
        return self._execute('decrypt', secret, secretfile)

    def _execute(self, cmd, secret, secretfile=None):
        tempdir = tempfile.gettempdir()
        secretfile_to_remove = False
        if secretfile is None:
            secretfile = os.path.join(tempdir, 'secretfile_%s' % time.time())
            with open(secretfile, 'w') as f:
                f.write(secret)
            secretfile_to_remove = True
        try:
            if self._passfile:
                self._execute_with_passfile(cmd, secretfile)
            if self._password:
                self._execute_with_password(cmd, secretfile)
            with open(secretfile) as f:
                return f.read()
        finally:
            if secretfile_to_remove:
                os.remove(secretfile)

    def _execute_with_passfile(self, cmd, secretfile):
        check_call(
            ['ansible-vault', '--vault-id', self._passfile, cmd, secretfile])

    def _execute_with_password(self, cmd, secretfile):
        proc = spawn(' '.join(['ansible-vault', cmd, secretfile]))
        confirm_password = cmd == 'encrypt'
        for _ in range(1 + confirm_password):
            proc.expect('.*password:')
            proc.sendline(self._password)
        proc.wait()
