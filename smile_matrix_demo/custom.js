$(document).ready(function(){
    /* Highlight the grand total of all matrix in blue every 2 seconds, but stop after 3 times */
    var counter = 0;
    var interval_id = setInterval(function(){
        $(".matrix td[id$='__grand_total']").effect("highlight", {'color': '#00f'}, 1000);
        if (++counter === 3) {
            window.clearInterval(interval_id);
        };
    }, 2 * 1000);
});
