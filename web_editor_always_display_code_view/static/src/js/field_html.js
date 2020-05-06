odoo.define('web_editor_always_display_code_view.field_html', function (require) {
'use strict';

    var FieldHtml = require('web_editor.field.html');
    var config = require('web.config');

    FieldHtml.include({
        /**
        * @override
        */
        _getWysiwygOptions: function () {
            var self = this;
            var wysiwygOptions = this._super();
            var superGenerateOptions = wysiwygOptions.generateOptions;
            wysiwygOptions.generateOptions = function (options) {
                var options = superGenerateOptions(options);
                var toolbar = options.toolbar || options.airPopover || {};
                if (!config.isDebug()) {
                    options.codeview = true;
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
                return options;
            }
            return wysiwygOptions;
        },
    });

});
