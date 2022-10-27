# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    'name': 'Smile Publish Document',
    'version': '1.0',
    'depends': [
        'attachment_indexation', 'website', 'smile_document'
    ],
    'author': 'Smile',
    'description': """
        Document Publish Management
    """,
    'summary': 'Smile Publish Document',
    'website': 'http://www.smile.fr',
    'category': 'Document Management',
    'sequence': 10,
    'data': [
        'views/document_view.xml',
        'views/attachments.xml',
        'views/attachments_templates.xml',
        'views/website_pages.xml',
        'views/menu.xml'
    ],
    'demo_xml': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
