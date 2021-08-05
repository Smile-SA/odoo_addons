# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Database Upgrade",
    "version": "0.2",
    "depends": ["web"],
    "author": "Smile",
    "license": 'LGPL-3',
    "description": """Smile Upgrade

Features

    * Allow to upgrade automatically database
    after code update and server restarting

Execution

    odoo.py -c <config_file> -d <db_name> --load=web,smile_upgrade

Configuration

    * Upgrades structure
        <project_directory>
        `-- upgrades
            |-- 1.1
            |   |-- __upgrade__.py
            |   |-- *.sql
            |   |-- *.py                    # only for post-load
            |   |-- *.csv                   # only for post-load
            |   `-- *.xml                   # only for post-load
            |-- 1.2
            |   |-- __upgrade__.py
            |   `-- *.sql
            `-- upgrade.conf

    * Upgrades configuration -- upgrade.conf
        [options]
        version=1.2

    * Upgrade configuration -- __upgrade__.py
        Content: dictonary with the following keys:
            * version
            * databases: let's empty if valid for all databases
            * translations_to_reload: language codes list to reload
            in post-load
            * description
            * modules_to_install_at_creation: modules list to install
            at database creation
            * modules_to_upgrade: modules list to update or install
            * pre-load: list of .sql files
            * post-load: list with .sql, .py, .csv and .xml files
                         with path .../filename (depending upgrades_path)
                         or module_name/.../filename

    * Python files in post-load
        Each Python file must have a function post_load_hook(env)

    * Odoo server configuration -- rcfile=~/.odoo_serverrc
        [options]
        upgrades_path = <project_directory>
        stop_after_upgrades = True if you want to stop server after upgrades
            else False

Additional features

    * In post-load, you can replace filename string by tuple
      (filename,
       'rollback_and_continue' or 'not_rollback_and_continue' or 'raise')
      -- default value = 'raise'

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "views/webclient_templates.xml",
    ],
    "qweb": [
        "static/src/xml/code_version.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
