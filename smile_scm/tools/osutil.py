# -*- coding: utf-8 -*-

from subprocess import os


class cd:
    """Context manager for changing the current working directory
    (http://stackoverflow.com/questions/431684/how-do-i-cd-in-python)"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = None
        while not self.savedPath:
            try:
                self.savedPath = os.getcwd()
            except OSError:
                os.chdir("..")
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
