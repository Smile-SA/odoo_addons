# -*- coding: utf-8 -*-

from random import choice
from string import ascii_letters, digits


def password_generator(size=8, chars=ascii_letters + digits):
    return ''.join(choice(chars) for _ in range(size))
