# -*- coding: utf-8 -*-

import json


def print_args(*args, **kwargs):
    res = json.dumps(args)[1:-1]
    if kwargs:
        if args:
            res += ', '
        res += ', '.join(['%s=%s' % (k, json.dumps(v)) for k, v in kwargs.iteritems()])
    return res
