# (C) 2024 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Hide Odoo Menu items",
    "version": "17.0.1.0.0",
    "depends": ["web_editor"],
    "author": "Smile",
    "license": "AGPL-3",
    "description": """""",
    "summary": "",
    "website": "",
    "category": "Tools",
    "sequence": 20,
    "assets": {
        "web.assets_backend": [
            "hide_odoo_menuitems/static/src/js/user_menu_items.js",
        ]
    },
    "auto_install": False,
    "installable": True,
    "application": False,
}
