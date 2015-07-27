// For copyright / license terms, see COPYRIGHT.rst (top level of repository)
// Repository: https://github.com/C3S/collecting_society.portal

$(document).on('click', '.navbar-collapse.collapse.in a:not(.dropdown-toggle)', function() {
    $(this).closest(".navbar-collapse").collapse('hide');
});
$(document).on('click', '.navbar-collapse.collapse.in button:not(.navbar-toggle)', function() {
    $(this).closest(".navbar-collapse").collapse('hide');
});