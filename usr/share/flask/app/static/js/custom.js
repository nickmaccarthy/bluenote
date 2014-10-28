
$(document).ready(function() {

    $("[data-toggle=tooltip]").tooltip();

    $('button[data-loading-text]').click(function () {
        $(this).button('loading');
    });

    // timeago fuzzy time plugin
    $('abbr.timeago').timeago();
});

window.setTimeout(function() {
    $(".flash-msg").fadeTo(500, 0).slideUp(500, function(){
        $(this).remove(); 
    });
}, 3000);

