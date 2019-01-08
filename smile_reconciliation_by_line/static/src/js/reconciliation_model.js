odoo.define('account.ReconciliationModelByLine', function (require) {
"use strict";
var StatementModel = require('account.ReconciliationModel').StatementModel;

return StatementModel.include({
    /**
     * Return the line that needs to be displayed by the widget
     *
     * @returns {Object} line that is loaded and not yet displayed
     */
  getStatementByLine: function () {
      var self = this;
      var linesToDisplay = _.pick(this.lines, function(value, key, object) {
          if (value.visible === true && self.alreadyDisplayed.indexOf(key) === -1 && value.id === self.context.reconciliation_by_line_id) {
                  self.alreadyDisplayed.push(key);
                  return object;
          }
      });
      return linesToDisplay;
  },
});
});

