// For copyright / license terms, see COPYRIGHT.rst (top level of repository)
// Repository: https://github.com/C3S/collecting_society.portal

$(document).ready(function(){
    $(".cs-fullscreen-toggle").click(function() {
        $(".cs-fullscreen-container").toggleClass('cs-fullscreen');
        $(".cs-fullscreen-toggle span").toggleClass('glyphicon-remove');
        $(".cs-fullscreen-toggle span").toggleClass('glyphicon-fullscreen');
    }); 
});