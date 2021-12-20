# -*- coding: utf-8 -*-
# (C) 2021 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile web hide groups",
    "version": "13.0.1",
    "depends": ["web"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    Add options on group in xml to manage to show/hide fields inside group

    How to use:

        * Default use (all fields inside groups is hidden):
        <group string="Test"
        options="{'active_show_hide': True}">

        * Add option default_show to active widget & show fields inside group by default
        <group string="Test"
        options="{'active_show_hide': True, 'default_show': True}">
    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        # Views
        "views/assets.xml",
    ],
    "qweb": [
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
