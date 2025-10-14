# -*- coding: utf-8 -*-

{
    "name": "Smile Test",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "description": """
Module used to execute Odoo tests in webservice.

This allows to launch tests without having to update modules,
and to compute code coveraged by tests.
""",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "license": "AGPL-3",
    "depends": ["base"],
    "auto_install": False,
    "external_dependencies": {
        "python": ["coverage"],
        "bin": ["flake8"],
    },
}
