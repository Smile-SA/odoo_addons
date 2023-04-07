/** @odoo-module **/


import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import Dialog from 'web.Dialog';

patch(FormController.prototype, "smile_confirmation", {
    setup() {
        this._super(...arguments);
        this.rpc = useService("rpc");
    },
    rpc_call(model, nameFunction, record_id, values) {
        return this.rpc("/web/dataset/call_kw/base/" + nameFunction, {
            model: model,
            method: 'get_message_informations',
            args: [[record_id], values],
            kwargs: {},
        });
    },

    async saveButtonClicked(params = {}) {
        const self = this;
        let index = 0;
        const record = this.model.root;
        const modelName = record['resModel'] ? record['resModel'] : false;
        const record_id = (record && record.data && record.data.id) ? record.data.id : false
        const recordID = record.__bm_handle__;
        const localData = self.model.__bm__.localData[recordID];
        const changes = localData._changes || {};
        self.rpc_call(modelName, 'get_message_informations', record_id, changes).then(function(results){
            display_popup(results);
        });

        async function save() {
            let saved = false;

            if (self.props.saveRecord) {
                saved = await self.props.saveRecord(record, params);
            } else {
                saved = await record.save();
            }
            self.enableButtons();
            if (saved && self.props.onSave) {
                self.props.onSave(record, params);
            }
            return saved;
        }

        function display_popup(popup_values){
            new Promise(function (resolve, reject) {
                if(typeof popup_values !== 'undefined' && typeof popup_values !== 'boolean' && popup_values.length){
                    if (popup_values[index].popup_type === 'confirm'){
                        Dialog.confirm(self, popup_values[index].message, {
                            title: popup_values[index].title,
                            confirm_callback: async () => {
                                index++;
                                if (popup_values.length > index){
                                    display_popup(popup_values);
                                }
                                else if (popup_values.length === index){
                                    self.rpc_call(modelName, 'execute_processing', record_id, changes).then(function(){
                                        save();
                                    });
                                }
                            }
                        }).on("closed", null, resolve);
                    }
                    else if (popup_values[index].popup_type === 'alert'){
                        Dialog.alert(self, popup_values[index].message, {title: popup_values[index].title});
                    }
                }else{
                    save();
                }
            });
        }
    }
});

