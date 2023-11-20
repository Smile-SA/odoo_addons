{
    "name": "Database Upgrade",
    "version": "17.0.0.0.0",
    "depends": ["web"],
    "author": "Smile",
    "license": "AGPL-3",
    "description": "",
    "summary": "",
    "website": "",
    "category": "Tools",
    "sequence": 20,
    "auto_install": True,
    "installable": True,
    "application": False,
    "assets": {
        "web.assets_backend": [
            "smile_upgrade/static/src/**/*",
        ],
    },
    "images": ["static/description/banner.gif"],
}
