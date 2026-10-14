{
    "name": "Smile Dynamic Action Visibility",
    "version": "20.0.1.0.0",
    "category": "Tools",
    "summary": "Hide actions and reports dynamically based on conditions",
    "description": "This module allows you to hide actions and reports"
    " dynamically using conditions per record.",
    "author": "Smile",
    "website": "https://www.smile.fr",
    "license": "AGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/security.xml",
        "security/ir.access.csv",
        "views/dynamic_action_rule_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "smile_dynamic_action_visibility/static/src/search/action_menus/"
            "action_menus.js",
        ],
    },
    "images": ["static/description/banner.gif"],
    "installable": True,
    "application": False,
}
