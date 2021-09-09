# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import binascii
import json


def print_args(*args, **kwargs):
    res = json.dumps(args)[1:-1]
    if kwargs:
        if args:
            res += ', '
        res += ', '.join('%s=%s' % (k, json.dumps(v))
                         for k, v in kwargs.items())
    return res


def b2a_int(data):
    return int(binascii.hexlify(data.encode('utf-8')), 16)


def a2b_int(intstr):
    hx = '%x' % intstr
    hx = hx.zfill(len(hx) + (len(hx) & 1))  # Make even length hex nibbles
    return binascii.unhexlify(hx).decode('utf-8')
