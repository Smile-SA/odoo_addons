# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from odoo.tests.common import TransactionCase


class ScriptTest(TransactionCase):

    def test_run_python(self):
        """
            Test the execution of a Python script.

            Prerequisites:
                - Create a smile.script record with Python type
                - Set a simple Python code that returns a string
                representation of partners

            Test:
                - Run the script in test mode

            Expected:
                - Check that the intervention state is 'done'
        """
        script = self.env['smile.script'].create({
            'name': 'TestPython',
            'type': 'python',
            'description': 'Test Python',
            'code': "result = str(self.env['res.partner'].search([]))",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertEqual(script.intervention_ids[0].state, 'done')

    def test_run_sql(self):
        """
            Test the execution of an SQL script.
            
            Prerequisites
                - Create a smile.script record with SQL type
                - Set a simple SQL query that concatenates strings
            
            Test:
                - Run the script in test mode
                
            Expected:
                - Check that the intervention state is 'done'
        """
        script = self.env['smile.script'].create({
            'name': 'TestSQL',
            'type': 'sql',
            'description': 'Test SQL',
            'code': "SELECT 'hello,' || 'world !';",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertEqual(script.intervention_ids[0].state, 'done')

    def test_run_xml(self):
        """
            Test the execution of an XML script.
    
            Prerequisites
                - Verify direct menu creation permissions
                - Create a smile.script record with XML type
                - Set XML code that creates a simple menu item
    
            Test:
                - Run the script in test mode
    
            Expected:
                - Check that interventions were created
                - Verify that the intervention state is 'done'
        """

        # First, let's check if we can create a menu directly
        # to verify permissions
        try:
            direct_menu = self.env['ir.ui.menu'].create({
                'name': 'Direct Test Menu',
                'parent_id': self.env.ref('base.menu_custom').id,
            })
            _logger.info(f"Direct menu creation successful: {direct_menu}")
            # Clean up after test
            direct_menu.unlink()
        except Exception as e:
            _logger.warning(f"Direct menu creation failed: {e}")

        # Now try with the script - using a very simple menu item tag
        script = self.env['smile.script'].create({
            'name': 'TestXML',
            'type': 'xml',
            'description': 'Test XML',
            'code': """
                <odoo>
                    <menuitem id="menu_test_script" 
                              name="Test Script Menu"
                              parent="base.menu_custom"/>
                </odoo>
            """,
        })
        _logger.info(f"Created script: {script}")

        script.with_context(do_not_use_new_cursor=True).run_test()

        if script.intervention_ids:
            intervention = script.intervention_ids[0]
            _logger.info(f"Intervention state: {intervention.state}")
            _logger.info(f"Intervention result: {intervention.result}")
        else:
            _logger.warning("No interventions created")

        self.assertTrue(script.intervention_ids,
                        "No interventions were created")

        if script.intervention_ids[0].state == 'done':
            _logger.info("XML script executed successfully")
        else:
            _logger.warning(
                f"XML script failed: {script.intervention_ids[0].result}")

        self.assertEqual(script.intervention_ids[0].state, 'done',
                         "The XML script should execute successfully")
