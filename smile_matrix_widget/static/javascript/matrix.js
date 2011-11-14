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
        $(".matrix tbody span[id^='row_total_']").each(function(){
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
        // Search up parents until we find level indication
        leveled_parent = $(elmnt).parentsUntil(".matrix", ".level").first();
        css_classes = $(leveled_parent).attr('class')
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
        console.log("We're at level " + level + " out of " + highest_level);

        // If we have all required resources, we are at the leaf of the resource tree, so we can create a new editable line
        if(level == highest_level){

            // Compute a new unique row index based on the other new rows in the matrix
            var new_row_index = 0;
            $(".matrix tr[id^='line_new']").each(function(){
                var row_id = parseInt($(this).attr("id").split("new")[1]);
                if(row_id > new_row_index){
                    new_row_index = row_id;
                };
            });
            new_row_index = "new" + (new_row_index + 1);

            // We are at the leaf: create a new editable line
            var new_row = line_template.clone(true).removeAttr('id').removeClass('template').hide();

            // TODO: Two lines can't share the same set of resources in the matrix
                    // Two lines can't share the same resource
//             if($(".matrix .resource input[value='" + res_id + "']").length > 0) {
//                 return;
//             };

            // Update our new row with its true values

            // Update the cells
            new_row.find(increment_cells_selector).each(function(){
                // Compute new cell and button ID
                name_fragments = $(this).attr("id").split("_");
                column_index = name_fragments[2];
                var new_cell_id = "cell_" + new_row_index + "_" + column_index;
                var new_button_id = "button_" + new_cell_id;
                // Apply new IDs and reset values
                $(this).attr('id', new_cell_id).attr('name', new_cell_id).val(cycling_values[0]);
                $(this).parent().find(increment_button_selector).first().attr('id', new_button_id).text(cycling_values[0]);
            });

            // Update the total column
            new_row.find("span[id^='row_total_']").attr('id', "row_total_" + new_row_index).text(cycling_values[0]);

            // Update the line ID
            $(new_row).attr('id', "line_" + new_row_index);

            // Update the resources
            new_row.find(".resource input").each(function(){
                // Replace the res_template_ prefix by our own
                var new_res_index = "res_" + new_row_index + $(this).attr('id').substring(12);
                $(this).attr('id', new_res_index).attr('name', new_res_index);
            });
            // TODO: use a loop for multi-resource lines
            new_row.find(".resource .name").text(res_name);
            new_row.find(".resource input").val(res_value);
            new_row.find(".resource input").attr('title', res_name);

        // We're in the middle of the matrix: display a new sub resource selector
        } else {
            // Get the template for that level
            var level_template = $(".matrix tbody tr.template.level_" + (level + 1));

            // Create a new row
            var new_row = level_template.clone(true).removeAttr('id').removeClass('template').hide();

            // TODO: update content

        };

        // By default the place we add our new stuff is at the end of the table
        var level_last_row = $(".matrix tbody tr:last");

        // Search the row in the table after which we'll add our new content
        if(level > 0){
            // Get the table row we're sitting in
            var current_table_row = $(this).parentsUntil("tbody").last();
            // Search the last row of the current level
            var level_last_row = current_table_row;
            var next_row_list = current_table_row.nextAll("tr:not(.template)");
            for(i = 0; i < next_row_list.length; i++){
                var next_row = next_row_list[i];
                var next_row_level = get_level($(next_row));
                console.log("next_row_level: " + next_row_level);
                if (next_row_level && next_row_level <= level){
                    break;
                };
                level_last_row = next_row;
            };
        };

        // Insert our new row at the end of the current level
        $(level_last_row).after(new_row.hide());
        $(new_row).fadeIn('fast');

        //TODO: $(deduplicate_new_line_selector());

    });


    // Deduplicate the add line list content with lines in the matrix
    function deduplicate_new_line_selector() {
        var displayed_lines = new Array();
        $(".matrix tr[id!='line_template'] .resource input").each(function(){
            displayed_lines.push(parseInt($(this).val()));
        });
        $(".matrix #resource_list option").each(function(){
            if ($.inArray(parseInt($(this).val()), displayed_lines) != -1) {
                $(this).hide();
            } else {
                $(this).show();
            };
        });
        $("#resource_list").val("default");
    };
    $(deduplicate_new_line_selector());


    // Activate delete row button
    $(".matrix .delete_row").click(function(){
        $(this).parent().parent().fadeOut('fast', function(){
            $(this).remove();
            $(deduplicate_new_line_selector());
            // TODO: update column totals
        });
    });


    // Activate the experimental timeline slider
    $(".matrix.slider").each(function(){
        // TODO
    });


});