# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile Document Version',
    'version': '13.0.1.0.0',
    'depends': [
        'attachment_indexation', 'smile_document'
    ],
    'author': 'Smile',
    'description': """
        Display document version
    """,
    'summary': 'Smile Document Version',
    'website': 'http://www.smile.fr',
    'category': 'Document Management',
    'sequence': 10,
    'data': [
        'views/document_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
