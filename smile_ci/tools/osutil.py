# -*- coding: utf-8 -*-

import os
import shutil


def mergetree(src, dst, symlinks=False, ignore=None):
    if not os.path.isdir(src):
        raise OSError(20, "Not a directory: '%s'" % src)
    if not os.path.exists(dst):
        shutil.copytree(src, dst, symlinks, ignore)
    else:
        names = os.listdir(src)
        ignored_names = ignore(src, names) if ignore is not None else set()
        for name in names:
            if name in ignored_names:
                continue
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            if os.path.isdir(srcname):
                mergetree(srcname, dstname, symlinks, ignore)
            elif os.path.isfile(srcname):
                if os.path.exists(dstname):
                    os.remove(dstname)
                if symlinks:
                    os.symlink(srcname, dstname)
                else:
                    shutil.copy2(srcname, dstname)
