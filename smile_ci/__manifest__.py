# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-2016 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Continuous Integration",
    "version": "2.0",
    "depends": [
        "smile_scm",
        "smile_base",
        "document",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "summary": "Test your Odoo app",
    "description": """
Continuous Integration
======================

Features

    # Update branch
        # For SVN repositories, configure the anonymous login/password
        # For Git repositories, add read access to the server via SSH key
    # Check if changes
    # Create build
    # Test build (set max_testing to limit concurrent testing builds)
        # Create Docker containers (Odoo server, database engine and other linked services)
        # Run daemonized Docker containers which starts server in test mode
        # Check code quality with flake8
        # Count lines of code with cloc
        # Create new database with demo or Restore dump in XML/RPC
        # Install modules in XML/RPC
        # Let Docker containers run until new builds kill it (set max_running to limit concurrent running builds)
    # Attach log / config / tests result / code coverage files to build
    # Parse build logs and store results in database

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & isabelle.richard@smile.fr
    """,
    "summary": "Build, Test",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/scm_security.xml",

        # Data
        "data/ir_config_parameter.xml",
        "data/docker_host.xml",
        "data/docker_registry.xml",
        "data/docker_image.xml",
        "data/scm.vcs.csv",
        "data/scm.version.csv",
        "data/scm_os.xml",
        "data/scm.version.package.csv",
        "data/ir_cron.xml",
        "data/mail_template.xml",

        # Views
        "views/scm_repository_branch_build_log_view.xml",
        "views/scm_repository_branch_build_coverage_view.xml",
        "views/scm_repository_branch_build_view.xml",
        "views/scm_repository_branch_view.xml",
        "views/scm_dashboard.xml",
        "views/scm_vcs_view.xml",
        "views/scm_version_view.xml",
        "views/scm_os_view.xml",
        "views/docker_host_view.xml",
        "views/docker_registry_view.xml",
        "views/docker_image_view.xml",
        "views/scm_menu.xml",
        "views/webclient_templates.xml",
        "wizards/docker_host_stats_view.xml",
    ],
    "demo": [
        "demo/scm.repository.csv",
        "demo/scm_repository_branch.xml",
        "demo/scm_repository_branch_clone.yml",
    ],
    "qweb": [
        'static/src/xml/kanban.xml',
        'static/src/xml/wizard.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': ['docker', 'flake8_debugger', 'flake8_print'],
    },
}
