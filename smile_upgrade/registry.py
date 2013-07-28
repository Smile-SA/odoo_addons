# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.modules.registry import RegistryManager

from upgrade import UpgradeManager

native_new = RegistryManager.new


@classmethod
def new(cls, db_name, force_demo=False, status=None, update_module=False, pooljobs=True):
    with UpgradeManager(db_name) as upgrade_manager:
        for upgrade in upgrade_manager.upgrades:
            upgrade.pre_load()
            native_new(db_name, update_module=upgrade.update_module, pooljobs=False)
            upgrade.post_load()
    return native_new(db_name, force_demo, status, update_module, pooljobs)

RegistryManager.new = new
