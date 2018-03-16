# -*- encoding: utf-8 -*-

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
    1. Tasks to do
    2. Views on which the checklist is visible
    3. Server Action executed if the checklist is completed
        * all action types: email, sms, object creation/update, etc

Known bugs

    Need to restart server for displaying, after creation,
    checklist on model's views

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": ['smile_filtered_from_domain'],
    "data": [
        'security/ir.model.access.csv',

        'data/act_actions_window.yml',

        'views/checklist_view.xml',
        'views/checklist_task_instance_view.xml',
        'views/checklist_view.xml',
        'views/menus.xml',
        'views/webclient_templates.xml',
    ],
    "demo": [
        'demo/checklist_demo.xml',
    ],
    "qweb": [
        'static/src/xml/checklist.xml',
    ],
    "test": [],
    "installable": True,
    "active": False,
}
