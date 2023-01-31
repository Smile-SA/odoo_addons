# (C) 2023 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Database Upgrade",
    "version": "15.0.0",
    "depends": ['web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": "",
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "auto_install": True,
    "installable": True,
    "application": False,
    'assets': {
        'web.assets_backend': [
            'smile_upgrade/static/src/**/*',
        ],
    },
}
