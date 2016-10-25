# -*- coding: utf-8 -*-

import docker
from functools import wraps


class MakeMoreResilient():

    def __init__(self, trial):
        self.trial = trial

    def __call__(self, func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            trial = self.trial
            while trial:
                try:
                    return func(*args, **kwargs)
                except:
                    trial -= 1
                    if not trial:
                        raise
        return wrapped


class Client(docker.Client):

    def __init__(self, trial=3, *args, **kwargs):
        self._trial = trial
        super(Client, self).__init__(*args, **kwargs)

    def __getattribute__(self, name):
        attr = super(Client, self).__getattribute__(name)
        if callable(attr):
            return MakeMoreResilient(self._trial)(attr)
        return attr

TLSConfig = docker.tls.TLSConfig
