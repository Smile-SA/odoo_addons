/** @odoo-module **/
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, proxy } from "@odoo/owl";

class DisplayCodeVersion extends Component {
    static template = "smile_upgrade.DisplayCodeVersion";

    setup() {
        this.orm = useService("orm");
        this.state = proxy({
            code_version: "",
        });
        this.orm.call("ir.code_version", "get_value").then((data) => {
            this.state.code_version = data;
        });
    }
}

export const systrayItem = {
    Component: DisplayCodeVersion,
    isDisplayed: () => {
        return user.isSystem;
    },
};

registry
    .category("systray")
    .add("DisplayCodeVersion", systrayItem, { sequence: 1 });
