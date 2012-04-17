jQuery(".matrix").ready(function(){

// console.profile("Matrix profiling");


    // Utility method to get the matrix element in which the provided object sit in
    function get_parent_matrix(elmnt){
        return jQuery(elmnt).parents(".matrix").first();
    };

    // Utility method to get increment values
    function get_increment_values(elmnt){
        return jQuery.parseJSON(jQuery("#" + get_parent_matrix(elmnt).attr("id") + "__increment_values").val());
    };

    // Utility method to parse the ID of field following our naming conventions
    function parse_id(field_id){
        var id_parts = new Array();
        // Extract the matrix ID
        var matrix = get_parent_matrix("#" + field_id);
        var matrix_id = matrix.attr("id");
        var matrix_prefix = matrix_id + "__";
        if(field_id.substring(matrix_prefix.length, 0) != matrix_prefix){
            alert("Matrix ERROR: field ID " + field_id + " should start with its matrix prefix " + matrix_prefix + " !");
            return;
        };
        id_parts.push(matrix_id);
        // Extract other field elements
        var parts = field_id.slice(matrix_prefix.length).split("_");
        if(jQuery.inArray(parts[0], ["res", "cell", "line", "column"]) == -1){
            alert("Matrix ERROR: field ID " + field_id + " is not a ressource, a cell, a line or a column !");
            return;
        };
        // If we're parsing a resource field id, then its ID elements past its 2 firsts compose a property ID.
        if(parts[0] == "res"){
            id_parts = id_parts.concat(parts.slice(0, 1));
            id_parts.push(parts.slice(2).join("_"));
        } else {
            id_parts = id_parts.concat(parts);
        };
        return id_parts;
    };


    // Selector expressions
    var increment_cells_selector = "input.increment[kind='float']";
    var increment_button_selector = ".button.increment";
    var global_increment_cells_selector = ".matrix " + increment_cells_selector;
    var global_increment_button_selector = ".matrix " + increment_button_selector;


    // Replace all integer fields of all matrix by a button template, then hide the original field
    var button_template = jQuery(".matrix .button.increment.template").first();
    jQuery(global_increment_cells_selector).each(function(i, cell){
        var $cell = jQuery(cell);
        $cell.after(jQuery(button_template).clone().removeClass('template').attr('id', 'button_' + $cell.attr("id")).text($cell.val())).hide();
    });


    // Label of buttons
    var buttons = jQuery(global_increment_button_selector);


    // Align the button and cell value to an available label
    // TODO: make this an original method and call it everytime we render a float. Apply this to totals too.
    buttons.each(function(i, button){
        var $button = jQuery(button);
        var cycling_values = get_increment_values($button);
        for(i = 0; i < cycling_values.length; i++){
            if(parseFloat($button.text()) == parseFloat(cycling_values[i])){
                $button.text(cycling_values[i]);
                $button.parent().find("input").val(cycling_values[i]);
                break;
            };
        };
    });


    // Cycles buttons
    buttons.click(function(){
        var button_value_tag = jQuery(this).parent().find("input");
        var button_label_tag = jQuery(this);
        var cycling_values = get_increment_values(jQuery(button_value_tag));
        var current_index = jQuery.inArray(parseFloat(button_value_tag.val()), cycling_values);
        var new_index = 0;
        if(!isNaN(current_index)) {
            new_index = (current_index + 1) % cycling_values.length;
        };
        var new_value = cycling_values[new_index];
        button_label_tag.text(new_value);
        button_value_tag.val(new_value);
        button_value_tag.trigger('change');
    });


    // Get cell value whatever the widget used to render it
    function get_cell_value(cell){
        return parseFloat(jQuery(cell).text());
    };


    // Set cell style dynamicaly
    function set_cell_style(cell, cell_value, threshold){
        if (!isNaN(threshold)) {
            if(cell_value > threshold){
                jQuery(cell).addClass("warning");
            } else {
                jQuery(cell).removeClass("warning");
            };
        };
        if(cell_value < 0){
            jQuery(cell).addClass("negative");
        } else {
            jQuery(cell).removeClass("negative");
        };
        if(!cell_value){
            jQuery(cell).addClass("zero");
        } else {
            jQuery(cell).removeClass("zero");
        };
        if (jQuery(cell).is(":visible")) {
            jQuery(cell).effect("highlight", {}, 100);
        };
    };


    // Update a column total
    function update_column_total(matrix_id, column_index){
        // Select all fields of the columns and sum them up
        var column_total = 0;
        // Only cells in the tbody of the table are sums up by columns
        jQuery("#" + matrix_id + " tbody [id*='__cell_'][id$='_" + column_index + "']").each(function(){
            cell_value = parseFloat(jQuery(this).val());
            if (!isNaN(cell_value)) {
                column_total += cell_value;
            };
        });
        // Get warning threshold
        var column_threshold = parseFloat(jQuery("#" + matrix_id + "__column_warning_threshold").first().val());
        // Update total content and style
        jQuery("#" + matrix_id + "__column_total_" + column_index).text(column_total).each(function(){
            set_cell_style(jQuery(this), column_total, column_threshold);
        });
    };


    // Update a row total
    function update_row_total(matrix_id, row_index){
        // Select all fields of the row and sum them up
        var row_total = 0;
        jQuery("#" + matrix_id + " table [id*='__cell_" + row_index + "_']").each(function(){
            cell_value = parseFloat(jQuery(this).attr('value'));
            if (!isNaN(cell_value)) {
                row_total += cell_value;
            };
        });
        jQuery("#" + matrix_id + "__row_total_" + row_index).text(row_total).each(function(){
            set_cell_style(jQuery(this), row_total);
        });
    };


    // Update grand total
    function update_grand_total(matrix_id){
        // Only compute grand totals from cells in the tbody
        var grand_total = 0;
        jQuery("#" + matrix_id + " tbody [id^='" + matrix_id + "__row_total_']:not([id^='" + matrix_id + "__row_total_dummy'])").each(function(){
            grand_total += parseFloat(jQuery(this).text());
        });
        jQuery("#" + matrix_id + "__grand_total").text(grand_total).each(function(){
            set_cell_style(jQuery(this), grand_total);
        });
    };


    // Compute columns and row totals
    jQuery(".matrix input[id*='__cell_'], .matrix select[id*='__cell_']").change(function(){
        // Get current cell coordinates
        var name_fragments = parse_id(jQuery(this).attr("id"));
        var matrix_id = name_fragments[0];
        var row_index = name_fragments[2];
        // Are we in the footer of the matrix ?
        var bottom_line = jQuery(this).parents("tfoot").length != 0;
        // Update all totals depending of that cell
        update_row_total(matrix_id, row_index);
        if(!bottom_line){
            var column_index = name_fragments[3];
            update_column_total(matrix_id, column_index);
            update_grand_total(matrix_id);
        };
    });


    // Utility method to get the level we're currently at
    function get_level(elmnt) {
        // If the provided element has no level indication, search its parents
        var leveled_parent = jQuery(elmnt);
        if(!jQuery(elmnt).hasClass("level")){
            leveled_parent = jQuery(elmnt).parentsUntil(".matrix", ".level").first();
        };
        css_classes = jQuery(leveled_parent).attr("class");
        if(css_classes){
            css_classes = css_classes.split(/\s+/);
            for(i = 0; i < css_classes.length; i++){
                c = css_classes[i];
                if(c.substring(6, 0) == "level_"){
                    level = c.split("_")[1];
                    if(!isNaN(level)){
                        return parseInt(level);
                    };
                };
            };
        };
        return;
    };


    // Utility method to parse the ID of field and get its resource
    function get_res_id(elmnt){
        return parse_id(jQuery(elmnt).attr("id")).slice(-1)[0];
    };


    // Make the add line button working
    // Create one new row for the selected resource
    jQuery(".matrix .button.add_row").click(function(){
        // Get the value selected in the associated select widget
        var selector = jQuery(this).parent().find("select").first();
        var new_res_data = selector.find("option:selected").first();
        var res_value = new_res_data.val();
        var res_name = new_res_data.text();
        if(isNaN(res_value)) {
            jQuery(selector).effect("shake", {times:3, direction:"left"}, 50);
            return;
        };
        res_value = parseInt(res_value);

        // Get the template of an editable line, i.e. the kind of matrix row we had at the leaf of the level tree
        var matrix = get_parent_matrix(jQuery(this));
        var matrix_id = matrix.attr("id");
        var line_template = matrix.find("tbody tr#" + matrix_id + "__line_template");
        var line_template_resources = jQuery(line_template).find("td.resource").first().find("input[id^='" + matrix_id + "__res_template_']");

        // Get the current and highest level
        var level = get_level(jQuery(this));
        var highest_level = line_template_resources.length - 1;

        var cycling_values = get_increment_values(jQuery(this));

        // Compute a new unique row index based on the other new rows in the matrix
        var new_row_index = 0;
        jQuery("tr[id^='" + matrix_id + "__line_new'],tr[id^='" + matrix_id + "__line_dummy']").each(function(){
            var id_parts = parse_id(jQuery(this).attr("id"));
            var line_id = id_parts[2];
            var split_by = "new";
            if(line_id.substring(10,5) == "dummy"){
                split_by = "dummy";
            };
            line_id = parseInt(line_id.split(split_by)[1]);
            if(line_id > new_row_index){
                new_row_index = line_id;
            };
        });
        new_row_index = new_row_index + 1;
        if(level == highest_level){
            new_row_index = "new" + new_row_index;
        } else {
            new_row_index = "dummy" + new_row_index;
        };

        // Get the ID of the resource from the ID of the selector: just remove the "res_list_" prefix
        var resource_id = parse_id(selector.attr("id")).slice(-1)[0];

        // If we have all required resources, we are at the leaf of the resource tree, so we can create a new editable line
        if(level == highest_level){

            // We are at the leaf: create a new editable line
            var new_row = line_template.clone(true).attr('id', matrix_id + "__line_" + new_row_index).removeClass('template');

            // Update the cells
            new_row.find("input[id*='__cell_'], select[id*='__cell_']").each(function(){
                var name_fragments = jQuery(this).attr("id").split("_");
                var column_index = name_fragments.slice(-1)[0];
                var new_cell_id = matrix_id + "__cell_" + new_row_index + "_" + column_index;
                jQuery(this).attr('id', new_cell_id).attr('name', new_cell_id).val(cycling_values[0]);
                // If there is a sibling button increment, update it too
                var new_button_id = "button_" + new_cell_id;
                jQuery(this).parent().find(increment_button_selector).attr('id', new_button_id).text(cycling_values[0]);
            });

        // We're in the middle of the matrix: display a new sub resource selector
        } else {
            // Get the template for that level
            var level_template = jQuery("#" + matrix_id + " tbody tr.template.level_" + (level + 1));
            // Create a new row
            var new_row = level_template.clone(true).attr('id', matrix_id + "__line_" + new_row_index).removeClass('template');
        };

        // Set row's label
        new_row.find(".resource .name").text(res_name);

        // Update the total column
        new_row.find("td[id*='__row_total_']").attr('id', matrix_id + "__row_total_" + new_row_index).text(cycling_values[0]);

        // If we're deeper than the first level, get the parent's resource value to populate our template later
        if(level > 0){
            // Get the table row we're sitting in
            var current_table_row = jQuery(this).parentsUntil("tbody").last();
            // Use parent's resource value to populate our template
            var parent_resources = new Array();
            jQuery(current_table_row).find(".resource input[id*='__res_']").each(function(){
                res_id = get_res_id(this);
                parent_resources[res_id] = {
                    "label": jQuery(this).attr("title"),
                    "value": jQuery(this).val(),
                    };
            });
        };

        // Update the local copy of resources
        new_row.find(".resource input[id*='__res_']").each(function(){
            res_id = get_res_id(this);
            // Only update the local resources ID on leafs: all others stays declared as template
            var new_res_index = matrix_id + "__res_" + new_row_index + "_" + res_id;
            jQuery(this).attr('id', new_res_index).attr('name', new_res_index);
            // Let local resources inherit values from its parent
            if(parent_resources && parent_resources[res_id]){
                jQuery(this).attr('value', parent_resources[res_id]['value']).attr('title', parent_resources[res_id]['label']);
            };
        });

        // Set value of the new resource field
        new_row.find(".resource input#" + matrix_id + "__res_" + new_row_index + "_" + resource_id).val(res_value).attr('title', res_name);

        // Search the row in the table after which we'll add our new content
        // By default the place we add our new stuff is at the start of the table
        var level_last_row = jQuery("#" + matrix_id + " tbody tr:first");
        if(level > 0){
            // Search the last row of the current level
            var level_last_row = current_table_row;
            current_table_row.nextAll("#" + matrix_id + " tbody tr:not(.template)").each(function(){
                var next_row_level = get_level(jQuery(this));
                if(next_row_level){
                    if(next_row_level <= level){
                        return false;
                    };
                    var level_last_row = jQuery(this);
                };
            });
        };

        // Insert our new row at the start of the sub-level: it enhance usability as it make the new row as close as the button we just clicked.
        // Beware of Firefox strange behaviour. See: http://api.jquery.com/fadeIn/#comment-47240324
        if(level > 0){
            new_row.insertAfter(level_last_row).hide().fadeIn('fast');
        } else {
            new_row.insertBefore(level_last_row).hide().fadeIn('fast');
        };

        // Force movement to current position to update new line cells visibility
        move_to_position(null, matrix_id);

        // Remove the entry from the selector
        jQuery(update_parent_selector(level_last_row.parent().find("[id='" + new_row.attr("id") + "']"), "hide"));
    });


    // Search the parent selector of the provided row and either show or hide there the entry carried by the row
    function update_parent_selector(table_row, action) {
        var table_row_level = get_level(jQuery(table_row));
        var matrix = get_parent_matrix(table_row);
        var matrix_id = matrix.attr("id");
        if(level > 1) {
            var parent_line = jQuery(table_row).prevAll("#" + matrix_id + " tbody tr.resource_line:not(.template)").first();
        } else {
            var parent_line = matrix.find(".toolbar").first();
        };
        var parent_selector = parent_line.find("select[id^='" + matrix_id + "__res_list_']").first();
        if (!parent_selector.length){
            return;
        };
        var selector_property = get_res_id(parent_selector);
        var res_value = jQuery(table_row).find("input[id$='_" + selector_property + "']").first().val();
        var option = parent_selector.find("option[value='" + res_value + "']");
        if(action == "hide") {
            option.hide();
        } else {
            option.show();
        };
        parent_selector.val("default");
        // Update selector look
        var visible_options = parent_selector.find("option").size();
        parent_selector.find("option").each(function(){
            if(jQuery(this).css("display") == "none"){
                visible_options--;
            };
        });
        if(visible_options > 1) {
            parent_selector.removeClass("readonlyfield").removeAttr("disabled");
            parent_selector.next(".add_row").show();
        } else {
            parent_selector.addClass("readonlyfield").attr("disabled", "disabled");
            parent_selector.next(".add_row").hide();
        };
    };


    // Remove lines rendered by Mako from their parent selectors
    jQuery(".matrix tbody tr:not(.template)").each(function(){
        jQuery(update_parent_selector(jQuery(this), "hide"));
    });


    // Activate delete row button
    jQuery(".matrix .delete_button").click(function(){
        jQuery(this).parentsUntil(".matrix", "tr").first().fadeOut('fast', function(){
            // Save the table body for late column totals update
            var matrix = get_parent_matrix(jQuery(this));
            var matrix_id = matrix.attr("id");
            // Un-hide the entry from its selector
            jQuery(update_parent_selector(jQuery(this), "show"));
            // Add row ID to the list of lines to remove
            var removed_lines_field_name = matrix_id + "__line_removed";
            var removed_lines = jQuery("#" + removed_lines_field_name).val() + jQuery(this).attr("id") + ',';
            jQuery("#" + removed_lines_field_name).val(removed_lines);
            // Force default value update as jQuery < 1.6 seems to mess with DOM attributes and properties
            document.getElementById(removed_lines_field_name).setAttribute('value', removed_lines);
            // Really remove the row
            jQuery(this).remove();
            // Force update of all column totals
            matrix.find("tfoot tr.total [id^='" + matrix_id + "__column_total_']").each(function(){
                var name_fragments = parse_id(jQuery(this).attr("id"));
                var column_index = name_fragments[name_fragments.length - 1];
                update_column_total(matrix_id, column_index);
            });
            // Update grand total
            update_grand_total(matrix_id);
        });
    });


    // Move the timeline by updating column visibility
    function move_to_position(new_position, matrix_id){
        // If not provided, get date range cells and navigation width dynamiccaly
        if (new_position == null) {
            var current_position = jQuery("#" + matrix_id + "__previous_cell").nextUntil("th:visible", "th:hidden").length + 1;
            new_position = current_position;
        };

        var date_range_cells = jQuery("#" + matrix_id + " th[id*='__column_label_']");
        var navigation_size = parseInt(jQuery("#" + matrix_id + "__navigation_size").first().val());

        // Compute the desired visibility of each cell
        var columns_to_show = new Array();
        var columns_to_hide = new Array();
        date_range_cells.each(function(i, cell){
            var $cell = jQuery(cell);
            var cell_position = i + 1;
            var column_index = parse_id($cell.attr("id"))[3];
            var column_cells_query = "#" + matrix_id + " .column_" + column_index;
            if (cell_position >= new_position && cell_position < new_position + navigation_size) {
                columns_to_show.push(column_cells_query);
            } else {
                columns_to_hide.push(column_cells_query);
            };
        });

        // Show and hide appropriate columns
        jQuery(columns_to_show.join(", ")).filter(":hidden").fadeIn('fast');
        jQuery(columns_to_hide.join(", ")).filter(":visible").hide();
    };


    // Catch action on navigation buttons and move the timeline accordingly
    jQuery(".matrix .button.navigation:not(.disabled)").click(function(){
        var matrix = get_parent_matrix(jQuery(this));
        var matrix_id = matrix.attr("id");

        // Compute positions
        var current_position = jQuery("#" + matrix_id + "__previous_cell").nextUntil("th:visible", "th:hidden").length + 1;
        var navigation_start = parseInt(jQuery("#" + matrix_id + "__navigation_start").first().val());
        var navigation_size = parseInt(jQuery("#" + matrix_id + "__navigation_size").first().val());
        var date_range_cells = jQuery("#" + matrix_id + " th[id*='__column_label_']");
        var farest_position  = date_range_cells.length - navigation_size + 1;

        // Detect direction
        var direction = jQuery(this).hasClass('next') ? 'next' : jQuery(this).hasClass('previous') ? 'previous' : jQuery(this).hasClass('start') ? 'start' : jQuery(this).hasClass('end') ? 'end' : 'center';

        // Compute new position
        var new_position = 0;
        if (direction == 'next') {
            new_position = current_position + 1;
        } else if(direction == 'previous') {
            new_position = current_position - 1;
        } else if(direction == 'start') {
            new_position = 1;
        } else if(direction == 'end') {
            new_position = farest_position;
        } else if(direction == 'center') {
            new_position = navigation_start;
        };

        // Check position constraints
        if (new_position < 1) {
            new_position = 1;
        };
        if (new_position > farest_position) {
            new_position = farest_position;
        };

        move_to_position(new_position, matrix_id);

        // XXX Sliding animation attempts
        // jQuery(query_column_cells(matrix_id, column_id_to_show)).effect('slide', {direction: direction == 'next' ? 'right' : 'left', mode: 'show'}, 'slow');
        // jQuery(query_column_cells(matrix_id, column_id_to_hide)).effect('slide', {direction: direction == 'next' ? 'left' : 'right', mode: 'hide'}, 'slow');

        // Navigation buttons
        var start_buttons    = jQuery("#" + matrix_id + " .button.navigation.start");
        var previous_buttons = jQuery("#" + matrix_id + " .button.navigation.previous");
        var center_buttons   = jQuery("#" + matrix_id + " .button.navigation.center");
        var next_buttons     = jQuery("#" + matrix_id + " .button.navigation.next");
        var end_buttons      = jQuery("#" + matrix_id + " .button.navigation.end");

        // Set navigation buttons style
        if (new_position <= 1) {
            start_buttons.addClass("disabled");
            previous_buttons.addClass("disabled");
        } else {
            start_buttons.removeClass("disabled");
            previous_buttons.removeClass("disabled");
        };
        if (new_position == navigation_start || navigation_size >= date_range_cells.length) {
            center_buttons.addClass("disabled");
        } else {
            center_buttons.removeClass("disabled");
        };
        if (new_position >= farest_position) {
            next_buttons.addClass("disabled");
            end_buttons.addClass("disabled");
        } else {
            next_buttons.removeClass("disabled");
            end_buttons.removeClass("disabled");
        };

        // Update total of cells hidden on the right or left side of the navigation slider
        var column_ids = [];
        jQuery("#" + matrix_id + " td[id^='" + matrix_id + "__navigation_righttotal_']").each(function() {
            column_ids.push(jQuery(this).attr("id").split('_').pop());
        });
        jQuery.each(column_ids, function(i, line_id) {
            jQuery.each(['right', 'left'], function(j, position) {
                // Get cells
                var partial_total_cell = jQuery("#" + matrix_id + "__navigation_" + position + "total_" + line_id);
                if (position == 'right'){
                    var hidden_columns = partial_total_cell.prevUntil("td:visible", "td:hidden");
                } else {
                    var hidden_columns = partial_total_cell.nextUntil("td:visible", "td:hidden");
                }
                // Compute the partial total
                var partial_total = 0;
                if (!hidden_columns.length) {
                    partial_total = '';
                } else {
                    hidden_columns.each(function(i, cell){
                        cell_value = get_cell_value(cell);
                        if (!isNaN(cell_value)) {
                            partial_total += cell_value;
                        };
                    });
                };
                // Update partial total content and style
                partial_total_cell.text(partial_total);
                set_cell_style(partial_total_cell, partial_total);
            });
        });

    });


    // Initialize the navigation slider
    jQuery(".matrix").each(function(){
        jQuery(this).find(".button.navigation.center").first().trigger('click');
    });


// console.profileEnd();

});
