import {patch} from "@web/core/utils/patch";
import {ActionMenus} from "@web/search/action_menus/action_menus";

patch(ActionMenus.prototype, {

    /**
     * Helper to get active IDs safely, checking if the prop exists.
     * The props to read from can be given explicitly: getActionItems() is
     * called with the next props by onWillUpdateProps, before this.props
     * is updated.
     */
    _getIds(props = this.props) {
        return (typeof props.getActiveIds === "function")
            ? props.getActiveIds()
            : [];
    },

    async getActionItems(props) {
        // 1. Call the original native method
        const items = await super.getActionItems(props);

        const resIds = this._getIds(props);

        const actionIds = items
            .map((item) => item.action?.id || item.id)
            .filter(Boolean);

        try {
            const invisibleIds = await this.orm.call(
                "ir.actions.actions",
                "get_invisible_action_ids",
                [props.resModel, resIds, actionIds]
            );

            return items.filter(
                (item) => !invisibleIds.includes(item.action?.id || item.id)
            );
        } catch (e) {
            console.error("Failed to filter actions:", e);
            return items; // Fallback to showing all if RPC fails
        }
    },

    async loadAvailablePrintItems() {
        const items = await super.loadAvailablePrintItems();
        const resIds = this._getIds();

        const actionIds = items.map((i) => i.action.id);
        try {
            const invisibleIds = await this.orm.call(
                "ir.actions.actions",
                "get_invisible_action_ids",
                [this.props.resModel, resIds, actionIds]
            );

            return items.filter((i) => !invisibleIds.includes(i.action.id));
        } catch (e) {
            console.error("Failed to filter actions:", e);
            return items; // Fallback to showing all if RPC fails
        }
    },
});
