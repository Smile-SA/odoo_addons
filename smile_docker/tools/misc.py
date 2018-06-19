# -*- coding: utf-8 -*-

import re

from odoo.addons.smile_scm.tools import strip_accents


def b2human(time):
    for delay, desc in [(1024**3, 'GiB'), (1024**2, 'MiB'), (1024, 'KiB')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "B"


def format_container(name, suffix=''):
    name = '%s_%s' % (name, suffix) if suffix else name
    match = re.compile('([/@. ])')
    return match.sub('_', strip_accents(name.lower()))


def format_image(image):
    return image.split('/')[-1].split(':')[0]


def format_repository_and_tag(repository):
    tag = ''
    if ':' in repository:
        image = repository.split('/')[-1]
        if ':' in image:
            tag = image.split(':')[-1]
            repository = repository[:-len(tag) - 1]
    return repository, tag


def format_repository(repository):
    return format_repository_and_tag(repository)[0]
