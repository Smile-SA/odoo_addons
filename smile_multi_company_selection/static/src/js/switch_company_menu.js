odoo.define('smile_multi_company_selection.SwitchCompanyMenu', function(require) {
    "use strict";

    var session = require('web.session');
    var SwitchCompanyMenu = require('web.SwitchCompanyMenu');

    SwitchCompanyMenu.include({
        events: {
            'click .dropdown-item[data-menu] div.log_into': '_onSwitchCompanyClick',
            'keydown .dropdown-item[data-menu] div.log_into': '_onSwitchCompanyClick',
            'click .dropdown-item[data-menu] div.toggle_company': '_onToggleCompanyClick',
            'keydown .dropdown-item[data-menu] div.toggle_company': '_onToggleCompanyClick',
            'click .toggle_all_company': '_onToggleAllCompanyClick',
            'click button.validate-choices': '_onValidateChoicesClick',
        },

        _onSwitchCompanyClick: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
        },

        /**
         * Disable the validation button if all companies are not checked.
         * Activate the validation button if at least one company is checked.
         *
         * @param dropdownItems companies div
         */
        activateValidateButton: function(dropdownItems) {
            if ($(dropdownItems).find('i').hasClass('fa-check-square')) {
                $('.validate-choices').prop('disabled', false);
            } else {
                $('.validate-choices').prop('disabled', true);
            }
        },

        _onToggleCompanyClick: function(ev) {
            if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            if (dropdownItem.find('.fa-square-o').length) {
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'true');
            } else {
                dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'false');
            }

            this.activateValidateButton(
                $(ev.currentTarget).closest('div.dropdown-menu').find('.dropdown-item'),
            );
        },

        _onToggleAllCompanyClick: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();

            // toggle class on all company checkbox
            var classToRemove = $(ev.currentTarget).hasClass('fa-square-o') ? 'fa-square-o' : 'fa-check-square';
            var classToAdd = $(ev.currentTarget).hasClass('fa-square-o') ? 'fa-check-square' : 'fa-square-o';
            $(ev.currentTarget).removeClass(classToRemove).addClass(classToAdd);

            // toggle class on one company checkbox
            $(ev.currentTarget).closest('div.dropdown-menu').find('.dropdown-item').each(function() {
                $(this).find('.' + classToRemove).removeClass(classToRemove).addClass(classToAdd);
                $(this).attr('aria-checked', 'true');
            });

            // activate or desactivate validate button if at least one company is checked or not
            this.activateValidateButton(
                $(ev.currentTarget).closest('div.dropdown-menu').find('.dropdown-item'),
            );
        },

        _onValidateChoicesClick: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var allowed_company_ids = this.allowed_company_ids;
            var current_company_id = allowed_company_ids[0];

            $(ev.currentTarget).closest('div.dropdown-menu').find('.dropdown-item').each(function() {
                var dropdownItem = $(this);
                var companyID = dropdownItem.data('company-id');
                if (dropdownItem.find('.fa-square-o').length) {
                    if (allowed_company_ids.includes(companyID)) {
                        allowed_company_ids.splice(allowed_company_ids.indexOf(companyID), 1);
                    }
                } else {
                    if (!allowed_company_ids.includes(companyID)) {
                        allowed_company_ids.push(companyID);
                    }
                }
            });
            session.setCompanies(current_company_id, allowed_company_ids);
        },

    });
});
