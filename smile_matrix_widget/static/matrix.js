$(document).ready(function(){
    $("input[kind!='boolean'][name^='cell_']:not(:disabled)").change(function(){
        name_fragments = $(this).attr("id").split("_");
        column_index = name_fragments[2];
        row_index = name_fragments[1];
        // Select all fields of the columns we clicked in and sum them up
        var column_total = 0;
        $("input[kind!='boolean'][name^='cell_'][name$='_" + column_index + "']:not(:disabled)").each(function(){
            column_total += parseFloat($(this).val());
        });
        $("tfoot span.column_total_" + column_index).text(column_total);
        // Select all fields of the row we clicked in and sum them up
        var row_total = 0;
        $("input[kind!='boolean'][name^='cell_" + row_index + "_']:not(:disabled)").each(function(){
            row_total += parseFloat($(this).val());
        });
        $("tbody span.row_total_" + row_index).text(row_total);
        // Compute the grand-total
        var grand_total = 0;
        $("tbody span[class^='row_total_']").each(function(){
            grand_total += parseFloat($(this).text());
        });
        $("#grand_total").text(grand_total);
    });
    $("tbody tr:first input[name^='cell_']:not(:disabled)").trigger('change');

    // Replace all integer fields by a button template, then hide the original field
    var button_template = $("#button_template");
    var cells = $("input[kind!='boolean'][name^='cell_']:not(:disabled)");
    cells.each(function(i, cell){
        var $cell = $(cell);
        $cell.after($(button_template).clone().attr('id', 'button_' + $cell.attr("id")).text($cell.val()));
        $cell.hide();
    });
    // Hide the button template
    $(button_template).hide();

    // Cycles buttons
    var cycling_values = ['0', '0.5', '1'];
    var buttons = $('.button.increment:not(:disabled)');
    buttons.click(function(){
        var button_value_tag = $(this).parent().find('input');
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

});