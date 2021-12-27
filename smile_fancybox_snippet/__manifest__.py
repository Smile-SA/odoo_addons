# -*- coding: utf-8 -*-
{
    'name': 'Fancybox Snippet',

    "version": "15.0.1.0.0",

    "author": "Smile",

    "website": 'http://www.smile.fr',

    "license": 'AGPL-3',

    "description": """
A snippet implementing jquery fancybox
    """,

    "category": "Tools",

    'depends': ['website'],

    'data': [
        'views/fancybox_snippet.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'smile_fancybox_snippet/static/less/fancybox.css',
        ],
        'web.assets_common': [
            'smile_fancybox_snippet/static/dist/jquery.fancybox.min.css',
            'smile_fancybox_snippet/static/dist/lightbox.min.css',
            'smile_fancybox_snippet/static/dist/jquery.fancybox.min.js',
            'smile_fancybox_snippet/static/dist/lightbox.min.js',
        ],
        'website.assets_editor': [
            'smile_fancybox_snippet/static/js/fancybox_snippet.js',
        ],
    },
}
