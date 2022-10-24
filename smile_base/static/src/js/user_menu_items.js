/** @odoo-module **/

import "@web/core/browser/feature_detection";
import { registry } from "@web/core/registry";

registry.category("user_menuitems").remove("documentation");
registry.category("user_menuitems").remove("support");
registry.category("user_menuitems").remove("odoo_account");
