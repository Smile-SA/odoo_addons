Smile addons for Odoo (formerly OpenERP)
========================

This repository contains a collection of Odoo modules.

Requirements
------------------------

* Odoo 14.0

# How to documentate your module

## Requirements

You need to install package `python-docutils`:

    apt install python3-docutils

## Write documentation

At the root of your module, define a file `README.md`.

As soon as `README.md` is finished, run the following command
at the root of the module:

    rst2html README.rst static/description/index.html
    sed -i 's/static\/description\///g' static/description/index.html


To update `index.html` of all modules, run the following command
at the root of the repository:

    for module in $(echo smile_*)
    do
        if [ -f "$module"/README.rst ]
        then
            rst2html "$module"/README.rst "$module"/static/description/index.html
            sed -i 's/static\/description\///g' "$module"/static/description/index.html
        fi
    done
