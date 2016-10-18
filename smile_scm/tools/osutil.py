# -*- coding: utf-8 -*-

import subprocess
from subprocess import os
from threading import Lock


class cd:
    def __init__(self, newPath):
        self._lock = Lock()
        self.newPath = newPath

    def __enter__(self):
        self._lock.acquire()
        self.savedPath = None
        while not self.savedPath:
            try:
                self.savedPath = os.getcwd()
            except OSError:
                os.chdir("..")
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
        self._lock.release()


def check_output_chain(args, stdin=None, stdout=None, stderr=None):
    previous_cmd = None
    cmd = []
    for arg in args:
        if arg != '|':
            cmd.append(arg)
        else:
            stdin = previous_cmd and previous_cmd.stdout or stdin
            previous_cmd = subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
            cmd = []
    stdin = previous_cmd and previous_cmd.stdout or stdin
    return subprocess.check_output(cmd, stdin=stdin, stderr=stderr)
