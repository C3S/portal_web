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

function hookFunction(object, functionName, callback) {
    (function(originalFunction) {
        object[functionName] = function () {
            var returnValue = originalFunction.apply(this, arguments);

            callback.apply(this, [returnValue, originalFunction, arguments]);

            return returnValue;
        };
    }(object[functionName]));
}

$(document).ready(function(){
    var form = $('.deform')
    if (form.length > 0) {
        var inputs = form.find('input');
        inputs.change(portal.preventExitPage)
        form.submit(portal.allowExitPage)
        if (deform && deform.DatatableSequence && deform.DatatableSequence.prototype)
        {
            hookFunction(deform.DatatableSequence.prototype, 'addRow', function() {
                portal.preventExitPage();
            });   
            hookFunction(deform.DatatableSequence.prototype, 'removeRow', function() {
                portal.preventExitPage();
            });  
            hookFunction(deform.DatatableSequence.prototype, 'createRow', function() {
                portal.preventExitPage();
            });  
            hookFunction(deform.DatatableSequence.prototype, 'editRow', function() {
                portal.preventExitPage();
            }); 
        }
    }    
})