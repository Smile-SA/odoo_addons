import { _t } from "@web/core/l10n/translation";
import { Plugin } from "@html_editor/plugin";
import { MAIN_PLUGINS } from "@html_editor/plugin_sets";

/**
 * Exposes the native alignment commands (html_editor AlignPlugin) in the
 * Powerbox and through keyboard shortcuts. The toolbar alignment menu is
 * provided natively since Odoo 20.
 */
class AlignTextPlugin extends Plugin {
    static id = "align_text";

    // Some editors remove the native AlignPlugin from MAIN_PLUGINS (e.g. the
    // website builder in translation mode): the native commands are then
    // unknown, so expose nothing.
    hasNativeAlign() {
        return (this.config.Plugins || MAIN_PLUGINS).some((P) => P.id === "align");
    }

    resources = this.hasNativeAlign()
        ? {
              shortcuts: [
                  { hotkey: "control+shift+l", commandId: "alignStart" },
                  { hotkey: "control+shift+c", commandId: "alignCenter" },
                  { hotkey: "control+shift+r", commandId: "alignEnd" },
                  { hotkey: "control+shift+j", commandId: "justify" },
              ],
              powerbox_items: [
                  {
                      categoryId: "structure",
                      commandId: "alignStart",
                      title: _t("Align Left"),
                      description: _t("Align text to the left"),
                      icon: "format_align_left",
                  },
                  {
                      categoryId: "structure",
                      commandId: "alignCenter",
                      title: _t("Align Center"),
                      description: _t("Center align text"),
                      icon: "format_align_center",
                  },
                  {
                      categoryId: "structure",
                      commandId: "alignEnd",
                      title: _t("Align Right"),
                      description: _t("Align text to the right"),
                      icon: "format_align_right",
                  },
                  {
                      categoryId: "structure",
                      commandId: "justify",
                      title: _t("Justify"),
                      description: _t("Justify text"),
                      icon: "format_align_justify",
                  },
              ],
          }
        : {};
}

// Register the plugin globally
MAIN_PLUGINS.push(AlignTextPlugin);
