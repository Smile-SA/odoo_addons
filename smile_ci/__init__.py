# -*- coding: utf-8 -*-

from . import contollers
from . import models

from odoo.addons.smile_docker.tools import exceptions as docker_exceptions
from odoo.addons.smile_scm.tools import exceptions as scm_exceptions


scm_exceptions.get_exception_message = docker_exceptions.get_exception_message
