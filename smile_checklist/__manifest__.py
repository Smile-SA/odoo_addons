# (C) 2022 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Checklist",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "license": 'AGPL-3',
    "description": """
Concept

    * Give visibility to users filling a form

Principle

    A checklist applies to a single object and is composed of:
    1. Tasks
        * List of fields to fill or boolean expressions to respect
        * Server Action executed if the task is completed
    2. Views on which the checklist is visible
    3. Server Action executed if the checklist is completed
        * all action types: email, sms, object creation/update, etc

Configuration

    * Please ensure that you launch server with option "-d" or checklist
        fields will not correctly be loaded



Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": [],
    "data": [
        'security/ir.model.access.csv',
        'views/checklist_task_instance_view.xml',
        'views/checklist_view.xml',
        'views/menus.xml',
    ],
    "demo": [
        'demo/checklist_demo.xml',
    ],
    'assets': {

        'web.assets_backend': [
            'smile_checklist/static/src/css/checklist.css',
            'smile_checklist/static/src/js/checklist.js',
            'smile_checklist/static/src/xml/checklist.xml',
        ],
    },
    "post_init_hook": 'post_init_hook',
    "test": [],
    "installable": True,
    "active": False,
}
