// dependancies
if(typeof deform == "undefined")
    throw new Error("'deform' is not included yet. exiting.");
// registry
if(typeof datatableSequences == "undefined")
    deform.datatableSequences = {};

/*
    Custom column attributes:

        datatableSequence: {
            position:     "displayed" | "collapsed" | "invisible"
            type:         "input" | "textarea" (default: "input")
            createValue:  string (default: "")
            createForm:   true | false (default: false)
            createShow:   true | false (default: false, shows field in table]
            createError:  true (mandantory) | function(value) -> true on error
            footerSearch: true | false (creates footer search field)
        }
*/

deform.DatatableSequence = function(vars) {

    /*** VARIABLES ***********************************************************/

    /* Self reference */
    var datatableSequence = this;

    /* Deform */
    this.oid = vars.oid;
    this.name = vars.name;
    this.minLen = parseInt(vars.minLen);
    this.maxLen = parseInt(vars.maxLen);
    this.nowLen = parseInt(vars.nowLen);
    this.orderable = (vars.orderable ? parseInt(vars.orderable) == 1 : false);
    this.proto = vars.proto;

    /* Datatable */
    this.api = vars.api;                // api url
    this.mode = "add";                  // "add"|"create"|"edit"
    this.events = {};                   // events to bind
    this.columns = vars.columns;        // custom datatable columns
    this.createForm = vars.createForm;  // create form for new rows
    this.unique = vars.unique;          // string (id column for unique rows) |
                                        // function(data) -> true if unique
    this.source = {                     // datatables source table
        tableId: "datatable_sequence_" + this.oid + "_source",
        header: typeof vars.sourceHeader == "string" ?
            vars.sourceHeader : "custom.add",
        table: false,  
        columns: {},
        events: [
            'header',
            'more',
            'search',
            'redraw',
        ],
    };  
    this.target = {                     // datatables target table
        tableId: "datatable_sequence_" + this.oid + "_target",
        header: typeof vars.targetHeader == "string" ?
            vars.targetHeader : "",
        table: false,
        columns: {},
        events: [
            'header',
            'more',
            'save',
            'redraw',
        ],
    };

    /*** AUXILIARY ***********************************************************/    

    /* Generates html code for the sequence (see addSequence() in deform.js) */
    this.newSequence = function(data) {
        var fieldmatch = /deformField(\d+)/;
        var namematch = /(.+)?-[#]{3}/;
        var html = decodeURIComponent(datatableSequence.proto);
        var $htmlnode = $(html);
        var $idnodes = $htmlnode.find('[id]');
        var $namednodes = $htmlnode.find('[name]');
        var genid = deform.randomString(6);
        var idmap = {};

        $idnodes.each(function(idx, node) {
            var $node = $(node);
            var oldid = $node.attr('id');
            var newid = oldid.replace(fieldmatch, "deformField$1-" + genid);
            $node.attr('id', newid);
            idmap[oldid] = newid;
            var labelselector = 'label[for=' + oldid + ']';
            var $fornodes = $htmlnode.find(labelselector);
            $fornodes.attr('for', newid);
            });

        $namednodes.each(function(idx, node) {
            var $node = $(node);
            var oldname = $node.attr('name');
            var newname = oldname.replace(fieldmatch, "deformField$1-" + genid);
            $node.attr('name', newname);
            });

        $(deform.callbacks).each(function(num, item) {
            var oid = item[0];
            var callback = item[1];
            var newid = idmap[oid];
            if (newid) { 
                callback(newid);
                }
            });

        deform.clearCallbacks();
        var e = jQuery.Event("change");
        $('#deform').trigger(e);

        if(data)
            datatableSequence.updateSequence($htmlnode, data);

        return $htmlnode.prop('outerHTML');
    };

    /* Is row already added? */
    this.rowAdded = function(data) {
        switch(typeof datatableSequence.unique) {
            case 'string':
                var added = false;
                var id = datatableSequence.unique;
                datatableSequence.target.table.rows().every(function() {
                    if(!added && this.data()[id] == data[id])
                        added = true;
                });
                return added;
            case 'function':
                return datatableSequence.unique(data);
            default:
                return false;
        }
    };

    /* Gets custom columns sorted by position */
    this.getSortedColumns = function() {
        var cols = {};
        $.each(['displayed', 'collapsed', 'invisible'], function(index, value) {
            cols[value] = $.grep(datatableSequence.columns, function(n, i) { 
                return n.datatableSequence.position == value;
            });
        });
        return cols;
    };

    /* Updates sequence with data */
    this.updateSequence = function(sequence, data) {
        if(!(sequence instanceof jQuery))
            sequence = $($.parseHTML(sequence));
        sequence.find("input[name='mode']").val(data.mode);
        $.each(datatableSequence.columns, function(index, column) {
            switch(column.datatableSequence.type) {
                case 'textarea':
                    var query = "textarea[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
                    break;
                case 'input':
                default:
                    var query = "input[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
            }
        });
        data.sequence = sequence.prop('outerHTML');
    };

    /* Updates row data and sequence with edit form data */
    this.updateData = function(data, form) {
        data.errors = "";
        $.each(datatableSequence.columns, function(index, column) {
            var element, value = false;
            switch(column.datatableSequence.type) {
                case 'textarea':
                    element = form.find("textarea[name='" + column.name + "']");
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
                    break;
                case 'input':
                default:
                    element = form.find("input[name='" + column.name + "']");
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
            }
        });
        datatableSequence.updateSequence(data.sequence, data);
    };

    /* Gets data template for created row */
    this.getDataTemplate = function() {
        var data = {
            mode: "create",
            errors: "",
        };
        $.each(datatableSequence.columns, function(index, column) {
            if(typeof column.datatableSequence.createValue == "undefined") {
                data[column.data] = "";
            } else {
                data[column.data] = column.datatableSequence.createValue;
            }
        });
        data.sequence = datatableSequence.newSequence(data);
        return data;
    };

    /* Is edit form valid? */
    this.editFormValid = function(form) {
        var valid = true;
        $.each(datatableSequence.columns, function(index, column) {
            if(typeof column.datatableSequence.createError == "undefined")
                return;
            if(column.datatableSequence.createError === true)
                column.datatableSequence.createError = function(value) {
                    return value === ""; };
            var element, value, group = false;
            switch(column.datatableSequence.type) {
                case 'textarea':
                    element = form.find("textarea[name='" + column.name + "']");
                    value = element.val();
                    group = element.closest('.form-group');
                    break;
                case 'input':
                default:
                    element = form.find("input[name='" + column.name + "']");
                    value = element.val();
                    group = element.closest('.form-group');
            }
            if(column.datatableSequence.createError(value)) {
                valid = false;
                group.addClass('has-error');
            } else {
                group.removeClass('has-error');
            }
        });
        return valid;
    };

    /*** ACTIONS *************************************************************/

    /* Adds a row */
    this.addRow = function(rowId) {
        // get data
        var data = datatableSequence.source.table.row(rowId).data();
        // prevent multiple addition
        if(datatableSequence.rowAdded(data))
            return false;
        // set data
        data.mode = "add";
        data.errors = "";
        data.sequence = datatableSequence.newSequence(data);
        // update table data
        datatableSequence.target.table.row.add(data).draw();
        return false;
    };

    /* Removes a row */
    this.removeRow = function(link) {
        // get row
        var row = datatableSequence.target.table.row($(link).parents('tr'));
        // remove always, if not in edit mode
        if(datatableSequence.mode == "add") {
            row.remove().draw();
            return false;
        }
        // remove only edited row in edit/create mode
        if(row.child()) {
            row.remove().draw();
            datatableSequence.mode = "add";
            return false;
        } else {
            // TODO: highlight open child
            return false;
        }
    };

    /* Creates a row */
    this.createRow = function() {
        // prevent multiple
        if(datatableSequence.mode !== "add") {
            // TODO: highlight open child
            return false;
        }
        datatableSequence.mode = "create";
        // set data template
        var data = datatableSequence.getDataTemplate();
        var row = datatableSequence.target.table.row.add(data).draw();
        // open edit area
        $(row.node()).find('a.edit').click();
        // catch enter key
        var child = $(row.node()).next('tr');
        var submit = $(child).find('.cs-datatables-apply');
        var input = $(child).find('input');
        $(input).keypress(function (e) {
            if (e.which == 13) {
                $(submit).click();
                return false;
            }
        });
        return false;
    };

    /* Edits a row */
    this.editRow = function(link) {
        // prevent multiple
        if(datatableSequence.mode == "edit") {
            // TODO: highlight open child
            return false;
        }
        if(datatableSequence.mode == "add")
            datatableSequence.mode = "edit";
        $(link).hide();
        var row = datatableSequence.target.table.row($(link).closest('tr'));
        row.child(datatableSequence.target.editDiv(row.data())).show();
        $(row.child()).addClass('child');
        return false;
    };

    /* Saves a row */
    this.saveRow = function(link) {
        // sanity check
        if(datatableSequence.mode === "add")
            return false;
        // validate edit form
        var child = $(link).parents('tr');
        var editForm = child.find(".cs-datatables-edit");
        if(!datatableSequence.editFormValid(editForm))
            return false;
        // update data
        var row = datatableSequence.target.table.row(child.prev('tr'));
        var data = row.data();
        datatableSequence.updateData(data, editForm);
        // update row
        row.data(data).draw();
        // close edit area
        row.child.remove();
        datatableSequence.mode = "add";
        return false;
    };

    /*** TEMPLATES ***********************************************************/

    this.target.tableNode = function() {
        var header = datatableSequence.target.header ?
            '<h3 class="datatable_sequence_' + datatableSequence.oid +
                '_target_header"></h3>' : '';
        var html = header +
            '<input type="hidden" name="__start__"' + 
                'value="' + datatableSequence.name + ':sequence" />' +
            '<table id="datatable_sequence_' + datatableSequence.oid + '_target"' +
                'class="table table-hover cs-datatables"></table>' +
            '<input type="hidden" name="__end__"' + 
                'value="' + datatableSequence.name + ':sequence" />';
        return html;
    };

    this.target.moreCol = function(data, type, row, meta) {
        var table = datatableSequence.target.table;
        if(!table)
            return '';
        if(data.mode === "create")
            return '<span class="label label-default" i18n:translate="">' +
                table.i18n('custom.new') + '</span>';
        var hasData = false;
        var isVisible = table.columns().responsiveHidden();
        table.row(meta.row).columns().every(function(index) {
            var name = datatableSequence.target.columns[index].name;
            if(!isVisible[index] && data[name])
                hasData = true;
        });
        return hasData ? 
            '<span class="more">' +
                '<span class="glyphicon glyphicon-zoom-in"></span>' +
            '</span>' : '';
    };

    this.target.moreDiv = function(api, rowIdx, columns) {
        var data = jQuery.map(columns, function(column, index) {
            if(!column.data)
                return '';
            return column.hidden ?
                '<tr data-dt-row="' + column.rowIndex + '" data-dt-column="' + 
                        column.columnIndex + '">' +
                    '<td>' + column.title + ':' + '</td> ' +
                    '<td>' + column.data + '</td>'+
                '</tr>' : '';
        }).join('');
        return data ? $('<table class="table"/>').append(data) : false;
    };

    this.target.editCol = function(data, type, row, meta) {
        var table = datatableSequence.target.table;
        if(!table)
            return '';
        return data.mode !== "add" ?
            '<a href="" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'editRow(this);" class="edit">' +
                '<span class="glyphicon glyphicon-pencil"></span> ' +
                table.i18n('custom.edit') +
            '</a>' : '';
    };

    this.target.editDiv = function(data) {
        var table = datatableSequence.target.table;
        var inputs = "";
        if(datatableSequence.createForm)
            inputs += datatableSequence.createForm(data);
        else
            $.each(datatableSequence.columns, function(index, column) {
                if(column.datatableSequence.createForm)
                    inputs += '' +
                        '<div class="form-group">' +
                            '<label class="control-label" for="' +
                                column.name + '">' +
                                column.title + '</label>' +
                            '<input name="' + column.name + '" ' +
                                'class="form-control" type="text" ' +
                                'value="' + data[column.name] + '">' +
                        '</div>';
            });
        var form = inputs +
            '<a href="#" class="cs-datatables-apply" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'saveRow(this);">' +
                '<button class="btn btn-info">' +
                    table.i18n('custom.apply') +
                '</button>' +
            '</a>';
        return $('<div class="cs-datatables-edit"/>').append(form);
    };

    this.target.showCol = function(data, type, row) {
        if(type !== 'display' && type !== 'filter')
            return data;
        if(row.mode === "create") {
            var html = "";
            $.each(datatableSequence.columns, function(index, column) {
                if(column.datatableSequence.createShow && row[column.name])
                    html += '<small>' + column.title + ':</small> ' +
                            row[column.name] + "<br>";
            });
            return html + row.errors;
        }
        return data;
    };

    this.target.removeCol = function(data, type, row, meta) {
        var table = datatableSequence.target.table;
        return table ?
            '<a href="#" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'removeRow(this);">' +
                '<span class="glyphicon glyphicon-minus"></span> ' +
                table.i18n('custom.remove') +
            '</a>' : '';
    };

    this.source.tableNode = function() {
        var header = datatableSequence.source.header ?
            '<h3 class="datatable_sequence_' + datatableSequence.oid +
                '_source_header"></h3>' : '';
        var footer = '<tfoot>';
        var search = false;
        $.each(datatableSequence.source.columns, function(index, column) {
            search = column.datatableSequence &&
                     column.datatableSequence.footerSearch === true;
            footer += search ?
                '<th class="multifilter">' + column.title + '</th>' :
                '<th></th>';
        });
        footer += '</tfoot>';
        var html = header +
            '<div class="container-fluid">' +
                '<table id="datatable_sequence_' + datatableSequence.oid + '_source"' +
                        'class="table table-hover cs-datatables">' +
                    footer +
                '</table>' +
            '</div>';
        return html;
    };

    this.source.moreCol = function(data, type, row, meta) {
        var table = datatableSequence.source.table;
        if(!table)
            return '';
        var isVisible = table.columns().responsiveHidden();
        var hasData = false;
        table.row(meta.row).columns().every(function(index) {
            var name = datatableSequence.source.columns[index].name;
            if(!isVisible[index] && data[name])
                hasData = true;
        });
        return hasData ? 
            '<span class="more">' +
                '<span class="glyphicon glyphicon-zoom-in"></span>' +
            '</span>' : '';
    };

    this.source.moreDiv = this.target.moreDiv;

    this.source.addCol = function(data, type, row, meta) {
        var table = datatableSequence.source.table;
        return table ?
            '<a href="#" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'addRow(' + meta.row + ');">' +
                '<span class="glyphicon glyphicon-plus"></span> ' +
                table.i18n('custom.add') +
            '</a>' : '';
    };

    /*** EVENTS **************************************************************/

    /* redraws the table after changing a tab */
    this.events.redraw = function(obj) {
        $("a[data-toggle=\"tab\"]").on("shown.bs.tab", function (e) {
            obj.table.columns.adjust();
        });
    };

    /* opens and closes the details */
    this.events.more = function(obj) {
        $("#" + obj.tableId + ' tbody').on('click', 'td.more', function() {
            var row = obj.table.row($(this).closest('tr'));
            var data = row.data();
            if(data.mode == "create")
                return;
            var isVisible = row.columns().responsiveHidden();
            var hasData = false;
            row.columns().every(function(index) {
                var name = obj.columns[index].name;
                if(!isVisible[index] && data[name])
                    hasData = true;
            });
            if(!hasData)
                return;
            if(row.child.isShown()) {
                row.child().show();
                $(this).html(
                    '<span class="glyphicon glyphicon-zoom-out" ' +
                        'aria-hidden="true"></span>'
                );
            } else {
                row.child(true);
                $(this).html(
                    '<span class="glyphicon glyphicon-zoom-in" ' +
                        ' aria-hidden="true"></span>'
                );
            }
        });
    };

    /* initialized the column search */
    this.events.search = function(obj) {
        $("#" + obj.tableId + ' tfoot th.multifilter').each(function () {
            var text = obj.table.i18n( 'custom.search' ) + " " + $(this).text();
            $(this).html('<input type="text" placeholder="' + text + '" />');
        });
        obj.table.columns().every(function () {
            var that = this;
            $('input', this.footer()).on('keyup change', function() {
                if (that.search() !== this.value) {
                    that.search( this.value ).draw();
                }
            });
        });
    };

    /* applies all open edit forms before submitting the form */
    this.events.save = function(obj) {
        $("#" + obj.tableId).closest("form").on('submit', function(){
            $(obj.table.table().node()).find("a.cs-datatables-apply").click();
        });
    };

    /* sets the header for the table */
    this.events.header = function(obj) {
        if(obj.header !== "")
            $('.' + obj.tableId + '_header').first().html(
                obj.table.i18n(obj.header));
        else
            $('.' + obj.tableId + '_header').remove();
    };

    /*** COLUMS **************************************************************/

    this.target.columns = (function() {
        var customCols = datatableSequence.getSortedColumns();
        // show created row data in first custom column
        customCols.displayed[0].render = datatableSequence.target.showCol;
        return [
            {
                name: "more",
                data: null,
                className: "text-center all more",
                width: "30px",
                orderable: false,
                searchable: false,
                render: datatableSequence.target.moreCol
            },
            customCols.displayed,
            {
                name: "edit",
                data: null,
                className: "text-right nowrap all",
                width: "60px",
                orderable: false,
                searchable: false,
                render: datatableSequence.target.editCol
            },
            {
                name: "remove",
                title:  '<a href="#" class="pull-right cs-thin"' +
                            'onclick="return deform.datatableSequences.' +
                                datatableSequence.oid + '.createRow();">' +
                            '<span class="glyphicon glyphicon-plus"></span> ' +
                            '<span i18n:translate="">Create</span>' +
                        '</a>',
                data: null,
                className: "text-right nowrap all",
                width: "100px",
                orderable: false,
                searchable: false,
                render: datatableSequence.target.removeCol
            },
            customCols.collapsed,
            {
                name: "sequence",
                data: "sequence",
                className: "sequence hidden",
                orderable: false,
                searchable: false,
            },
            customCols.invisible,
            {
                name: "mode",
                data: "mode",
                visible: false,
                orderable: false,
                searchable: false,
            },
            {
                name: "errors",
                data: "errors",
                visible: false,
                orderable: false,
                searchable: false,
            }
        ].flat();
    })();

    this.source.columns = (function() {
        var customCols = datatableSequence.getSortedColumns();
        return [
            {
                name: "more",
                data: null,
                className: "text-center all more",
                width: "30px",
                orderable: false,
                searchable: false,
                render: datatableSequence.source.moreCol
            },
            customCols.displayed,
            {
                name: "add",
                data: null,
                width: "100px",
                className: "text-right nowrap all",
                orderable: false,
                searchable: false,
                render: datatableSequence.source.addCol
            },
            customCols.collapsed,
            customCols.invisible,
        ].flat();
    })();

    /*** INIT ****************************************************************/

    this.init = function() {

        // initialization
        $(document).ready(function() {

            // generate html
            var htmlNode = ".datatable_sequence_" + datatableSequence.oid;
            $(htmlNode).append(datatableSequence.target.tableNode());
            $(htmlNode).append(datatableSequence.source.tableNode());
            
            // initialize target table
            datatableSequence.target.table = $(
                "#" + datatableSequence.target.tableId).DataTable({
                data: $(".datatable_sequence_" + datatableSequence.oid).data('rows'),
                language: $(".datatable_sequence_" + datatableSequence.oid).data('lang'),
                paging: false,
                info: false,
                searching: false,
                autoWidth: false,
                fixedHeader: true,
                responsive: {
                    details: {
                        renderer: datatableSequence.target.moreDiv,
                        type: 'column'
                    }
                },
                columns: datatableSequence.target.columns,
                order: [
                    [ 8, "desc" ],  // create rows at the top
                    [ 1, "asc" ]    // first displayed row
                ]
            });
            
            // initialize source table
            datatableSequence.source.table = $(
                "#" + datatableSequence.source.tableId).DataTable({
                language: $(".datatable_sequence_" + datatableSequence.oid).data('lang'),
                processing: true,
                serverSide: true,
                searchDelay: 600,
                autoWidth: false,
                fixedHeader: true,
                ajax: {
                    type: "POST",
                    contentType: "application/json; charset=utf-8",
                    url: datatableSequence.api,
                    xhrFields: {withCredentials: true},
                    dataType: "json",
                    data: function(args) {
                        args.group = false;
                        return JSON.stringify(args);
                    }
                },
                responsive: {
                    details: {
                        renderer: datatableSequence.source.moreDiv,
                        type: 'column'
                    }
                },
                columns: datatableSequence.source.columns,
                order: [
                    [ 1, "asc" ]  // first displayed row
                ]
            });

            // redraw (to display zoom icon in more column)
            datatableSequence.target.table.rows().invalidate('data').draw(false);

            // add events
            $.each([datatableSequence.source, datatableSequence.target],
                function(_, obj) {
                $.each(obj.events, function(_, event) {
                    datatableSequence.events[event](obj);
                });
            });

            // add datatable sequence to registry (for global access)
            deform.datatableSequences[datatableSequence.oid] = datatableSequence;

        });
    };

};
