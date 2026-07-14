/** @odoo-module **/
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

class DisplayCodeVersion extends Component {
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
    isDisplayed: () => {
        return user.isSystem;
    },
};

registry
    .category("systray")
    .add("DisplayCodeVersion", systrayItem, { sequence: 1 });
