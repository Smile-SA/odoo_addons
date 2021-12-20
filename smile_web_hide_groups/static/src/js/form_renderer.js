odoo.define('board.BoardView', function (require) {
"use strict";

    var FormRenderer = require('web.FormRenderer');
    var pyUtils = require('web.py_utils');

    FormRenderer.include({
        _renderInnerGroup: function (node) {
            var $result = this._super.apply(this, arguments);
            var options = node.attrs.options ? pyUtils.py_eval(node.attrs.options) : {};
            if (options.active_show_hide) {
                var defaultIcon = options.default_show || this.mode !== 'readonly' ? 'fa-minus-circle' : 'fa-plus-circle';
                if (node.attrs.string) {
                    var col = parseInt(node.attrs.col, 10) || this.INNER_GROUP_COL;
                    $result.find('tr:first').replaceWith($('<tr><td colspan="' + col + '" style="width: 100%;"><div class="o_horizontal_separator">' + node.attrs.string + ' <button class="fa ' + defaultIcon + ' btn-show-hide-group"></button></div></td></tr>'));
                }
                if (this.mode === 'readonly' && !options.default_show) {
                    $result.find('tr').not(':first').hide();
                }
                $result.find('.btn-show-hide-group').click(function(event) {
                    $result.find('tr').not(':first').toggle();
                    $(this).toggleClass('fa-plus-circle fa-minus-circle');
                    event.preventDefault();
                });
            }
            return $result;
        },
    });

});
