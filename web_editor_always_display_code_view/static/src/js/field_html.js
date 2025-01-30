odoo.define('web_editor_always_display_code_view.field_html', function (require) {
'use strict';

    var FieldHtml = require('web_editor.field.html');
    var config = require('web.config');

    FieldHtml.include({
        /**
        * @override
        */
        _getWysiwygOptions: function () {
            var wysiwygOptions = this._super();
            var superGenerateOptions = wysiwygOptions.generateOptions;
            wysiwygOptions.generateOptions = function (options) {
                var optionsSuper = superGenerateOptions(options);
                var toolbar = optionsSuper.toolbar || optionsSuper.airPopover || {};
                if (!config.isDebug()) {
                    optionsSuper.codeview = true;
                    var view = _.find(toolbar, function (item) {
                        return item[0] === 'view';
                    });
                    if (view) {
                        if (!view[1].includes('codeview')) {
                            view[1].splice(-1, 0, 'codeview');
                        }
                    } else {
                        toolbar.splice(-1, 0, ['view', ['codeview']]);
                    }
                }
                return optionsSuper;
            };
            return wysiwygOptions;
        },
    });

});
