# -*- coding: utf-8 -*-
# (C) 2017 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "filtered_from_domain",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module allows to filter records from a search domain.

Example:
    records.filtered_from_domain([
        ('state', '=', 'draft'),
        ('line_ids.product_id.name', '=', 'My product'),
    ])

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "http://www.smile.fr",
    'category': 'Tools',
    "sequence": 0,
    "data": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
