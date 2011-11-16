$(document).ready(function(){

    // Selector expressions
    var increment_cells_selector = "input[kind='float'][class='increment'][name^='cell_']:not(:disabled)";

    var increment_button_selector = ".button.increment:not(:disabled)";
    var global_increment_cells_selector = ".matrix " + increment_cells_selector;
    var global_increment_button_selector = ".matrix " + increment_button_selector;


    // Replace all integer fields by a button template, then hide the original field
    var button_template = $("#matrix_button_template");
    var cells = $(global_increment_cells_selector);
    cells.each(function(i, cell){
        var $cell = $(cell);
        $cell.after($(button_template).clone().removeClass('template').attr('id', 'button_' + $cell.attr("id")).text($cell.val()));
        $cell.hide();
    });

    // Label of buttons
    var cycling_values = ['0', '0.5', '1'];
    var buttons = $(global_increment_button_selector);


    // Align the button and cell value to an available label
    // TODO: make this an original method and call it everytime we render a float. Apply this to totals too.
    buttons.each(function(i, button){
        var $button = $(button);
        for(i = 0; i < cycling_values.length; i++){
            if(parseFloat($button.text()) == parseFloat(cycling_values[i])){
                $button.text(cycling_values[i]);
                $button.parent().find("input").val(cycling_values[i]);
                break;
            };
        };
    });


    // Compute float totals
    $(global_increment_cells_selector).change(function(){
        name_fragments = $(this).attr("id").split("_");
        column_index = name_fragments[2];
        row_index = name_fragments[1];
        // Select all fields of the columns we clicked in and sum them up
        var column_total = 0;
        $(".matrix input[kind!='boolean'][name^='cell_'][name$='_" + column_index + "']:not(:disabled)").each(function(){
            column_total += parseFloat($(this).val());
        });
        $("#column_total_" + column_index).text(column_total).effect("highlight", function(){
            if(column_total > 1){
                $(this).addClass("warning");
            } else {
                $(this).removeClass("warning");
            };
        });
        // Select all fields of the row we clicked in and sum them up
        var row_total = 0;
        $(".matrix input[kind!='boolean'][name^='cell_" + row_index + "_']:not(:disabled)").each(function(){
            row_total += parseFloat($(this).val());
        });
        $("#row_total_" + row_index).text(row_total).effect("highlight");
        // Compute the grand-total
        var grand_total = 0;
        $(".matrix tbody td[id^='row_total_']").each(function(){
            grand_total += parseFloat($(this).text());
        });
        $("#grand_total").text(grand_total).effect("highlight");
    });


    // Compute boolean totals
    // TODO: merge this with the code above
    $("input[type='hidden'][kind='boolean'][name^='cell_']:not(:disabled)").change(function(){
        name_fragments = $(this).attr("id").split("_");
        column_index = name_fragments[2];
        row_index = name_fragments[1];
        // Select all fields of the row we clicked in and sum them up
        var row_total = 0;
        $(".matrix input[type='hidden'][kind='boolean'][name^='cell_" + row_index + "_']:not(:disabled)").each(function(){
            cell_value = parseFloat($(this).val());
            if (!isNaN(cell_value)) {
                row_total += cell_value;
            };
        });
        $("#row_total_" + row_index).text(row_total).effect("highlight");
    });


    // Cycles buttons
    buttons.click(function(){
        var button_value_tag = $(this).parent().find("input");
        var button_label_tag = $(this);
        var current_index = $.inArray(button_value_tag.val(), cycling_values);
        var new_index = 0;
        if(!isNaN(current_index)) {
            new_index = (current_index + 1) % cycling_values.length;
        };
        var new_value = cycling_values[new_index];
        button_label_tag.text(new_value);
        button_value_tag.val(new_value);
        button_value_tag.trigger('change');
    });


    // Utility method to get the level we're currently at
    function get_level(elmnt) {
        // If the provided element has no level indication, search its parents
        var leveled_parent = $(elmnt);
        if(!$(elmnt).hasClass("level")){
            leveled_parent = $(elmnt).parentsUntil(".matrix", ".level").first();
        };
        css_classes = $(leveled_parent).attr('class');
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
        l = $(elmnt).attr("id").split("_");
        var res_id = new Array();
        for(i = 2; i < l.length; i++){
            res_id.push(l[i]);
        };
        return res_id.join("_");
    };


    // Make the add line button working
    // Create one new row for the selected resource
    $(".matrix .button.add_row").click(function(){
        // Get the value selected in the associated select widget
        var selector = $(this).parent().find("select").first();
        var new_res_data = selector.find("option:selected").first();
        var res_value = new_res_data.val();
        var res_name = new_res_data.text();
        if(isNaN(res_value)) {
            $(selector).effect("shake", {times:3, direction:"left"}, 50);
            return;
        };
        res_value = parseInt(res_value);

        // Get the template of an editable line, i.e. the kind of matrix row we had at the leaf of the level tree
        var line_template = $(".matrix tbody tr#line_template");
        var line_template_resources = $(line_template).find("td.resource").first().find("input[id^='res_template_']");

        // Get the current and highest level
        var level = get_level($(this));
        var highest_level = line_template_resources.length - 1;

        // Compute a new unique row index based on the other new rows in the matrix
        var new_row_index = 0;
        $(".matrix tr[id^='line_new'],.matrix tr[id^='line_dummy']").each(function(){
            var row_id = $(this).attr("id");
            var split_by = "new";
            if(row_id.substring(10,5) == "dummy"){
                split_by = "dummy";
            };
            row_id = parseInt(row_id.split(split_by)[1]);
            if(row_id > new_row_index){
                new_row_index = row_id;
            };
        });
        new_row_index = new_row_index + 1;
        if(level == highest_level){
            new_row_index = "new" + new_row_index;
        } else {
            new_row_index = "dummy" + new_row_index;
        };

        // Get the ID of the resource from the ID of the selector: just remove the "resource_list_" prefix
        var resource_id = get_res_id(selector);

        // If we have all required resources, we are at the leaf of the resource tree, so we can create a new editable line
        if(level == highest_level){

            // We are at the leaf: create a new editable line
            var new_row = line_template.clone(true).attr('id', "line_" + new_row_index).removeClass('template');

            // TODO: Two lines can't share the same set of resources in the matrix
                    // Two lines can't share the same resource
//             if($(".matrix .resource input[value='" + res_id + "']").length > 0) {
//                 return;
//             };

            // Update the cells
            new_row.find("td.float input[id^='cell_']").each(function(){
                name_fragments = $(this).attr("id").split("_");
                column_index = name_fragments[2];
                var new_cell_id = "cell_" + new_row_index + "_" + column_index;
                $(this).attr('id', new_cell_id).attr('name', new_cell_id).val(cycling_values[0]);
                // If there is a sibling button increment, update it too
                var new_button_id = "button_" + new_cell_id;
                $(this).parent().find(increment_button_selector).attr('id', new_button_id).text(cycling_values[0]);
            });

        // We're in the middle of the matrix: display a new sub resource selector
        } else {
            // Get the template for that level
            var level_template = $(".matrix tbody tr.template.level_" + (level + 1));
            // Create a new row
            var new_row = level_template.clone(true).attr('id', "line_" + new_row_index).removeClass('template');
        };

        // Set row's label
        new_row.find(".resource .name").text(res_name);

        // Update the total column
        new_row.find("td[id^='row_total_']").attr('id', "row_total_" + new_row_index).text(cycling_values[0]);

        // If we're deeper than the first level, get the parent's resource value to populate our template later
        if(level > 0){
            // Get the table row we're sitting in
            var current_table_row = $(this).parentsUntil("tbody").last();
            // Use parent's resource value to populate our template
            var parent_resources = new Array();
            $(current_table_row).find(".resource input[id^='res_']").each(function(){
                res_id = get_res_id(this);
                parent_resources[res_id] = {
                    "label": $(this).attr("title"),
                    "value": $(this).val(),
                    };
            });
        };

        // Update the local copy of resources
        new_row.find(".resource input[id^='res_']").each(function(){
            res_id = get_res_id(this);
            // Only update the local resources ID on leafs: all others stays declared as template
            var new_res_index = "res_" + new_row_index + "_" + res_id;
            $(this).attr('id', new_res_index).attr('name', new_res_index);
            // Let local resources inherit values from its parent
            if(parent_resources && parent_resources[res_id]){
                $(this).attr('value', parent_resources[res_id]['value']).attr('title', parent_resources[res_id]['label']);
            };
        });

        // Set value of the new resource field
        new_row.find(".resource input[id^='res_" + new_row_index + "_" + resource_id + "']").val(res_value).attr('title', res_name);

        // Search the row in the table after which we'll add our new content
        // By default the place we add our new stuff is at the start of the table
        var level_last_row = $(".matrix tbody tr:first");
        if(level > 0){
            // Search the last row of the current level
            var level_last_row = current_table_row;
            current_table_row.nextAll(".matrix tbody tr:not(.template)").each(function(){
                var next_row_level = get_level($(this));
                if(next_row_level){
                    if(next_row_level <= level){
                        return false;
                    };
                    var level_last_row = $(this);
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

        // Remove the entry from the selector
        $(update_parent_selector(level_last_row.parent().find("[id='" + new_row.attr("id") + "']"), "hide"));

    });


    // Search the parent selector of the provided row and either show or hide there the entry carried by the row
    function update_parent_selector(table_row, action) {
        var table_row_level = get_level($(table_row));
        if(level > 1) {
            var parent_line = $(table_row).prevAll(".matrix tbody tr.resource:not(.template)").first();
        } else {
            var parent_line = $(table_row).parent().parent().parent().find(".toolbar").first();
        }
        var parent_selector = parent_line.find("select[id^='resource_list_']").first();
        var selector_property = get_res_id(parent_selector);
        var res_value = $(table_row).find("input[id$='_" + selector_property + "']").first().val();
        var option = parent_selector.find("option[value='" + res_value + "']");
        if(action == "hide") {
            option.hide();
        } else {
            option.show();
        };
        parent_selector.val("default");
    };


    // Remove lines rendered by Mako from their parent selectors
    $(".matrix tbody tr:not(.template)").each(function(){
        $(update_parent_selector($(this), "hide"));
    });


    // Activate delete row button
    $(".matrix .delete_row").click(function(){
        $(this).parentsUntil(".matrix", "tr").first().fadeOut('fast', function(){
            // Save the table body for late column totals update
            var matrix_body = $(this).parentsUntil(".matrix", "tbody");
            // Un-hide the entry from its selector
            $(update_parent_selector($(this), "show"));
            // Really remove the row
            $(this).remove();
            // Force update of column totals
            matrix_body.find("tr:first [id^='cell_']").trigger("change");
        });
    });


    // Activate the experimental timeline slider
    $(".matrix.slider").each(function(){
        // TODO
    });


});