$(document).ready(function(){
    /* Highlight in blue grand total of all matrix every 2 seconds */
    setInterval(function(){
        $(".matrix td[id$='__grand_total']").effect("highlight", {'color': '#00f'}, 1000);
    }, 2 * 1000);
});
