{
    'name': 'Auto Refresh',
    'version': '0.1',
    'depends': [
        'web',
        'bus',
        'mail',
    ],
    'author': 'Fisher Yu, Smile',
    'website': 'http://www.smile.fr',
    'license': 'AGPL-3',
    'description': """
Web Auto Refresh
----------------

This module is a fork of web_auto_refresh developped by Fisher Yu on Odoo v10.
This fork works with all non-edited views, not only with kanban and list views.

To test this module, you need to:
1. go to Setting > Technical > Actions > Window Actions, find the desired action, activate the auto search Check box
2. add one automated action for the target model, add the following python code,
    this automated action can be applied(when to run) to creation, update or delete per your requirement
    model.env['bus.bus'].sendone('auto_refresh', model._name)

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    'category': 'Tools',
    'sequence': 20,
    'data': [
        'views/webclient_templates.xml',
    ],
    'qweb': [],
    'auto_install': True,
    'installable': True,
    'application': False,
}
