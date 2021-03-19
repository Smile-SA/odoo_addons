================
WebService Queue
================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/13.0/smile_web_impex
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module adds helpers to implement a queue job.

This adds the mechanism of keeping jobs inside a queue, and treat them
one at a time periodically, with a restart policy in case of failures.

You have to define your model with your own method, a cron to execute the
jobs in queue, and define views to consult job history.

This module could be greatly improved, feel free to make it better via
pull requests.

**Table of contents**

.. contents::
   :local:

Usage
=====

Define your model
~~~~~~~~~~~~~~~~~

You have to define a class inheriting from `queue.job`.

.. code-block:: python

   class MyModuleJob(models.Model):
      _name = 'my_module.job'
      _inherit = 'queue.job'

      method = fields.Selection([
         ('foo', 'Method doing foo'),
         ('bar', 'Method doing bar')
      ])

      def foo(self):
         """Execute the job `foo`.
         This could be a button method, a cron method, etc.
         """
         pass

      def bar(self):
         """Execute the job `bar`.
         This could be a button method, a cron method, etc.
         """
         pass

Execution of queue
~~~~~~~~~~~~~~~~~~

You have to define a cron to check queue periodically, eg. each 5 minutes:

.. code-block:: xml

   <record id="some_external_api_queue" model="ir.model.export.template">
      <field name="name">Some external API</field>
      <field name="model_id" ref="my_module.model_my_module_job" />
      <field name="method">execute_call</field>
      <field name="filter_type">method</field>
      <field name="filter_method">filter_jobs</field>
      <field name="unique" eval="False" />
      <field name="new_thread" eval="False" />
      <field name="one_at_a_time" eval="True" />
   </record>

   <record id="ir_cron_some_external_api_queue" model="ir.cron">
      <field name="name">Some external API - Manage queue</field>
      <field name="user_id" ref="base.user_root" />
      <field name="interval_number">5</field>
      <field name="interval_type">minutes</field>
      <field name="numbercall">-1</field>
      <field name="priority">10</field>
      <field name="nextcall" eval="time.strftime('%Y-%m-%d %H:00:00')" />
      <field name="model_id" ref="my_module.model_my_module_job" />
      <field name="code">model.execute_cron()</field>
      <field name="state">code</field>
   </record>

   <record id="some_external_api_queue" model="ir.model.export.template">
      <field name="cron_id" ref="ir_cron_some_external_api_queue" />
   </record>

Consult jobs enqueued
~~~~~~~~~~~~~~~~~~~~~

You have to define views and actions to see your jobs.

Following code displays pending and error jobs by default:

.. code-block:: xml

   <record id="view_job_form" model="ir.ui.view">
      <field name="name">my_module.job.form</field>
      <field name="model">my_module.job</field>
      <field name="arch" type="xml">
         <form>
            <header>
               <field name="state" widget="statusbar"/>
            </header>
            <sheet>
               <group col="1">
                  <field name="method"/>
               </group>
               <group col="6">
                  <field name="max_tries"/>
                  <field name="tries"/>
                  <field name="total_tries"/>
               </group>
               <group>
                  <field name="status_code"/>
                  <field name="result"/>
               </group>
            </sheet>
         </form>
      </field>
   </record>

   <record id="view_job_tree" model="ir.ui.view">
      <field name="name">my_module.job.tree</field>
      <field name="model">my_module.job</field>
      <field name="arch" type="xml">
         <tree string="Jobs" decoration-danger="state=='error'"
               decoration-success="state=='done'"
               decoration-muted="state=='canceled'">
            <field name="method" />
            <field name="state" />
            <field name="status_code" />
            <field name="create_date" />
            <field name="execute_date" />
            <field name="total_tries" />
         </tree>
      </field>
   </record>

   <record id="view_job_search" model="ir.ui.view">
      <field name="name">my_module.job.search</field>
      <field name="model">my_module.job</field>
      <field name="arch" type="xml">
         <search>
            <field name="method" />
            <filter name="filter_canceled" string="Canceled"
               domain="[('state', '=', 'canceled')]" />
            <filter name="filter_done" string="Done"
               domain="[('state', '=', 'done')]" />
            <filter name="filter_error" string="Error"
               domain="[('state', '=', 'error')]" />
            <filter name="filter_pending" string="Pending"
               domain="[('state', '=', 'pending')]" />
            <filter name="groupby_state" string="State"
               context="{'group_by': 'state'}" />
            <filter name="groupby_status_code" string="Status code"
               context="{'group_by': 'status_code'}" />
         </search>
      </field>
   </record>

   <record id="action_jobs_view" model="ir.actions.act_window">
      <field name="name">Some external API</field>
      <field name="type">ir.actions.act_window</field>
      <field name="res_model">my_mobule.job</field>
      <field name="view_mode">tree,form</field>
      <field name="context">{
         'search_default_filter_pending': 1,
         'search_default_filter_error': 1
      }</field>
   </record>

   <menuitem id="menu_wsqueue_jobs_some_external_api"
      action="action_jobs_view" parent="smile_wsqueue.menu_wsqueue_jobs" />

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_web_impex%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Paul JOANNON
* Isabelle RICHARD

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
