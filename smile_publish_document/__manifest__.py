# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    'name': 'Smile Publish Document',
    'version': '20.0.1.0.0',
    'depends': [
        'website', 'smile_document'
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
    "images": ["static/description/banner.gif"],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
