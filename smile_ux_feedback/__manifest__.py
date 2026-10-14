{
    "name": "UX Feedback",
    "version": "20.0.1.0.0",
    "depends": ["base", "web"],
    "author": "Smile",
    "license": "AGPL-3",
    "description": (
        "This module provides a feedback mechanism for users to input their "
        "performance, conformity, satisfaction, and general feedback "
        "on various pages of the Odoo back office. It includes a pop-up "
        "interface that captures user details and timestamps."
    ),
    "summary": "Module to collect user feedback on Odoo back office pages.",
    "website": "http://smile.fr",
    "category": "Tools",
    "sequence": 20,
    "auto_install": False,
    "installable": True,
    "application": True,
    "data": [
        # Security
        "security/ux_feedback_groups.xml",
        "security/ir.access.csv",
        # Views
        "views/ux_feedback_views.xml",
        "views/ux_feedback_config_performance_views.xml",
        "views/ux_feedback_config_satisfaction_views.xml",
        "views/ux_feedback_config_conformity_views.xml",
        "views/ux_feedback_config_menu_views.xml",

        # Data
        "data/ux_feedback_conformity_data.xml",
        "data/ux_feedback_satisfaction_data.xml",
        "data/ux_feedback_performance_data.xml",
        # Wizards
        "wizard/ux_feedback_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "smile_ux_feedback/static/src/js/ux_feedback.js",
            "smile_ux_feedback/static/src/js/ux_feedback.xml",
        ],
    },
    "images": ["static/description/banner.gif"],
}
