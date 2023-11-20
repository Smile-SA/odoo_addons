/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";

class DisplayCodeVersion extends Component {
    static components = {
        ...Component.components,
        Dropdown,
        DropdownItem,
    };
    setup() {
        this.orm = useService("orm");
        const self = this;
        self.state = useState({
            code_version: "",
        });
        self.orm.call("ir.code_version", "get_value").then(function (data) {
            Object.assign(self.state, { code_version: data });
        });
    }
}
DisplayCodeVersion.template = "smile_upgrade.DisplayCodeVersion";
DisplayCodeVersion.props = {};

export const systrayItem = {
    Component: DisplayCodeVersion,
    isDisplayed: (env) => env.services.user.isSystem,
};

registry
    .category("systray")
    .add("DisplayCodeVersion", systrayItem, { sequence: 1 });
