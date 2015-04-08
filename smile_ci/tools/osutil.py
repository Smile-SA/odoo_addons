# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import shutil
import subprocess


def mergetree(src, dst, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            if not os.path.exists(dstname):
                os.makedirs(dstname)
            mergetree(srcname, dstname, ignore)
        else:
            if os.path.exists(dstname):
                os.remove(dstname)
            shutil.copy2(srcname, dstname)


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
