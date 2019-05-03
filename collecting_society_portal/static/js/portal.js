// For copyright / license terms, see COPYRIGHT.rst (top level of repository)
// Repository: https://github.com/C3S/collecting_society.portal

portal = {
    'preventExitPage': function(event) {
        window.onbeforeunload = function() {
            return 'You made changes to a field. Are you sure you want to leave this page?';}
    },
    'allowExitPage': function(event) {
        window.onbeforeunload = function() {
            return;
        }
    }
}

$(document).ready(function(){
    var form = $('.deform')
    if (form.length > 0) {
        var inputs = form.find('input');
        inputs.change(portal.preventExitPage)
        form.submit(portal.allowExitPage)
    }    
})