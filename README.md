Smile addons for Odoo (formerly OpenERP)
========================

This repository contains a collection of Odoo modules.

Requirements
------------------------

* Odoo 10.0 EE

# How to documentate your module

## Requirements

You need to install package `python-docutils`::

    apt install python-docutils

## Write documentation

At the root of your module, define a file `README.md`.

As soon as `README.md` is finished, run the following command
at the root of the module::

    rst2html.py README.rst static/description/index.html
