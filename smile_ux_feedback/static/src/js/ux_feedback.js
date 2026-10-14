import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";
import {onWillStart} from "@odoo/owl";

export class FeedbackIcon extends Component {
    static template = "smile_ux_feedback.FeedbackIcon";

    setup() {
        this.action = useService("action");
        this.user = user;
        this.ShowFeedbackIcon = false;

        onWillStart(async () => {
            if (this.user) {
                this.ShowFeedbackIcon = await user.hasGroup("smile_ux_feedback.group_ux_feedback_user");
            }
        });
    }

    openFeedbackWizard() {
        this.action.doAction("smile_ux_feedback.action_feedback_wizard", {
            additionalContext: {
                default_url: window.location.href,
            },
        });
    }
}

export const systrayItem = {
    Component: FeedbackIcon,
};

registry.category("systray").add(
    "ux_feedback.FeedbackIcon", systrayItem, {sequence: 1000});
