{
    "name": "Web Editor Text Alignment Commands",
    "version": "20.0.0.0.0",
    "summary": "Add text alignment commands to the WYSIWYG editor Powerbox",
    "description": "This module adds text alignment options to the WYSIWYG editor Powerbox.",
    "category": "Tools",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "license": 'AGPL-3',
    "depends": ["web", "html_editor"],
    "assets": {
        'web.assets_backend': [
            'smile_odoo_editor_align/static/src/js/align_plugin.js',
        ],
    },
    "images": ["static/description/banner.gif"],
    "installable": True,
    "application": False,
    "auto_install": True,
}
