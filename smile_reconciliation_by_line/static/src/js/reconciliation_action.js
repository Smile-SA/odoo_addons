odoo.define('account.ReconciliationClientActionByLine', function (require) {
"use strict";

var ReconciliationClientAction = require('account.ReconciliationClientAction');
var core = require('web.core');
/**
 * Widget used as action for 'account.bank.statement' reconciliation
 */
var StatementActionByLine = ReconciliationClientAction.StatementAction.extend({
    /**
     * append the renderer and instantiate the line renderer
     *
     * @override
     */
    start: function () {
        var self = this;
        this.set("title", this.title);
        var breadcrumbs = this.action_manager && this.action_manager.get_breadcrumbs() || [{ title: this.title, action: this }];
        this.update_control_panel({breadcrumbs: breadcrumbs, search_view_hidden: true}, {clear: true});
        this.renderer.prependTo(self.$('.o_form_sheet'));
        this._renderLines();
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    /**
     * render line widget and append to view
     *
     * @private
     */
    _renderLines: function () {
        var self = this;
        var l;
        var linesToDisplay = this.model.getStatementByLine();
        for(l in linesToDisplay){
           if (linesToDisplay[l].id == self.params.context.reconciliation_by_line_id){
                _.each(linesToDisplay, function (line, handle) {
                                    var widget = new self.config.LineRenderer(self, self.model, line);
                                    widget.handle = handle;
                                    self.widgets.push(widget);
                                    widget.appendTo(self.$('.o_reconciliation_lines'));
                        });
           if (this.model.hasMoreLines() === false) {
                    this.renderer.hideLoadMoreButton();
                    }
              }
        }
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    /**
     * call 'changeName' model method
     *
     * @private
     * @param {OdooEvent} event
     */
    _onChangeName: function () {
        var self = this;
        var title = event.data.data;
        this.model.changeName(title).then(function () {
            self.title = title;
            self.set("title", title);
            self.renderer.update({
                'valuenow': self.model.valuenow,
                'valuemax': self.model.valuemax,
                'title': title,
            });
        });
        setTimeout(function () { location.reload(false); }, 2000);
    },
    /**
     * call 'validate' or 'autoReconciliation' model method then destroy the
     * validated line and update the action renderer with the new status bar
     * values and notifications then open the first available line
     * @private
     * @param {OdooEvent} event
     */
    _onValidate: function (event) {
        var self = this;
        var handle = event.target.handle;
        var method = event.name.indexOf('auto_reconciliation') === -1 ? 'validate' : 'autoReconciliation';
        this.model[method](handle).then(function (result) {
            self.renderer.update({
                'valuenow': self.model.valuenow,
                'valuemax': self.model.valuemax,
                'title': self.title,
                'time': Date.now()-self.time,
                'notifications': result.notifications,
                'context': self.model.getContext(),
            });
            _.each(result.handles, function (handle) {
                self._getWidget(handle);
                var index = _.findIndex(self.widgets, function (widget) {return widget.handle===handle;});
                self.widgets.splice(index, 1);
            });
            // Get number of widget and if less than constant and if there are more to laod, load until constant
            if (self.widgets.length < self.model.defaultDisplayQty
                && self.model.valuemax - self.model.valuenow >= self.model.defaultDisplayQty) {
                var toLoad = self.model.defaultDisplayQty - self.widgets.length;
                self._loadMore(toLoad);
            }
        });
        setTimeout(function () { location.reload(false); }, 2000);
    },
});

core.action_registry.add('bank_statement_reconciliation_byline_view', StatementActionByLine);

return StatementActionByLine
});
