// dependancies
if(typeof deform == "undefined")
    throw new Error("'deform' is not included yet. exiting.");
// registry
if(typeof datatableSequences == "undefined")
    deform.datatableSequences = {};

/*
    Deform Datatables Widget

    This class aids the integration of jquery datatables and deform sequences.
    It generates two datatables: One target table with the current sequence
    (one row is one sequence item) and one source table (ajax datasource) with
    rows to add to the sequence. The serialized sequece item for colander is
    saved into a row cell of the target table. Additionally new sequence items
    might be created and edited.
    
    Html:

        <div class="datatable_sequence_${oid}"
            data-rows="${rows}" data-lang="${lang}"></div>

    Initialization:

        var datatableSequence = new deform.DatatableSequence({
            oid: "${oid}",
            name: "${name}",
            minLen: "${min_len}",
            maxLen: "${max_len}",
            nowLen: "${now_len}",
            proto: "${prototype}",
            api: "${api}/<PATH>",
            unique: "<COLUMNNAME>" | function(data) -> true if unique,
            columns: [<DATATABLECOLUMNS>],
        }).init();

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

    TODO:
    - orderable rows
    - min/max rows
    - this.target.editDiv: switch for input types (input, textarea, etc.)
    - layover for edit rows?
    - layover for add row?
    - highlighting of edit div on clicks on deactivated controls?
*/

deform.DatatableSequence = function(vars) {

    /*** VARIABLES ***********************************************************/

    // self reference
    var datatableSequence = this;

    // deform (passed from sequence template)
    this.oid = vars.oid;
    this.name = vars.name;
    this.minLen = parseInt(vars.minLen);
    this.maxLen = parseInt(vars.maxLen);
    this.nowLen = parseInt(vars.nowLen);
    this.orderable = (vars.orderable ? parseInt(vars.orderable) == 1 : false);
    this.proto = vars.proto;
    this.api = vars.api;

    // datatable
    this.mode = "add";                  // "add" | "create" | "edit"
    this.events = {};                   // events to bind
    this.columns = vars.columns;        // custom datatable columns
    this.createForm = vars.createForm;  // create form for new rows
    this.unique = vars.unique;          // string (id column for unique rows) |
                                        // function(data) -> true if unique
    this.target = {                     // datatables target table meta object
        tableId: "datatable_sequence_" + this.oid + "_target",
        header: typeof vars.targetHeader == "string" ?
            vars.targetHeader : "",
        table: false,                   // datatables source table
        columns: {},                    // columns (filled on init)
        events: [                       // events of this.events (bound on init)
            'setHeader',
            'setCreateText',
            'more',
            'save',
            'redraw',
        ],
    };
    this.source = {                     // datatables source table meta object
        tableId: "datatable_sequence_" + this.oid + "_source",
        header: typeof vars.sourceHeader == "string" ?
            vars.sourceHeader : "custom.add",
        table: false,                   // datatables source table
        columns: {},                    // columns (filled on init)
        events: [                       // events of this.events (bound on init)
            'setHeader',
            'more',
            'search',
            'redraw',
        ],
    };  

    /*** AUXILIARY ***********************************************************/    

    /* 
        Escapes html characters for display.

        Args:
          str (string): Unescaped string.

        Returns:
          string: Escaped string.
    */
    this.escape = function(str) {
        return jQuery('<div />').text(str).html();
    };

    /* 
        Generates html code for the data of a new sequence item.

        If data is provided, the sequence gets updated.

        Note:
          This function is based on addSequence() in deform.js

        Args:
          data (array, optional): Datatables row data.

        Returns:
          string: Html code for serialized sequence item data.

    */
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

    /* 
        Checks, if a row already added.

        Args:
          data (array): Datatables row data.

        Returns:
          true: If row is already added.
          false: Otherwise.
    */
    this.rowAdded = function(data) {
        switch(typeof datatableSequence.unique) {
            // the column name is provided as a string
            case 'string':
                var added = false;
                var id = datatableSequence.unique;
                datatableSequence.target.table.rows().every(function() {
                    if(!added && this.data()[id] == data[id])
                        added = true;
                });
                return added;
            // a custom function for the data is provided
            case 'function':
                return datatableSequence.unique(data);
            default:
                return false;
        }
    };

    /*
        Gets custom columns sorted by position.

        Custom columns are the columns provided by the user as init parameter.
        They are merged with other functional columns on initialization. The
        positions denote the slots, where they should be included.
        The positions are:
          - displayed: Visible main columns
          - collapsed: Collapsed columns, visible by clicking the more column
          - invisible: Invisible columns used for hidden data

        Returns:
          dictionary: {
            'displayed': array of displayed columns,
            'collapsed': array of collapsed columns,
            'invisible': array of invisible columns
          }
    */
    this.getSortedColumns = function() {
        var cols = {};
        $.each(['displayed', 'collapsed', 'invisible'], function(index, value) {
            cols[value] = $.grep(datatableSequence.columns, function(n, i) { 
                return n.datatableSequence.position == value;
            });
        });
        return cols;
    };

    /* 
        Updates sequence item html code with row data.

        Args:
          sequence (jQuery node): Node containing the sequence item html code.
          sequence (string): Html code for sequence item data.
          data (array): Datatables row data.
    */
    this.updateSequence = function(sequence, data) {
        // parse string if sequence is not a jquery node object
        if(!(sequence instanceof jQuery))
            sequence = $($.parseHTML(sequence));
        // update mode
        sequence.find("input[name='mode']").val(data.mode);
        // update data columns
        $.each(datatableSequence.columns, function(index, column) {
            switch(column.datatableSequence.type) {
                // update textareas
                case 'textarea':
                    var query = "textarea[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
                    break;
                // update input fields
                case 'input':
                default:
                    var query = "input[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
            }
        });
        // save updated html code back into the row data again
        data.sequence = sequence.prop('outerHTML');
    };

    /*
        Updates row data and sequence item html code with edit form data.

        Args:
          data (array): Datatables row data.
          form (jQuery node): Node containing the form fields
    */
    this.updateData = function(data, form) {
        data.errors = "";
        // update data columns
        $.each(datatableSequence.columns, function(index, column) {
            var element, value = false;
            switch(column.datatableSequence.type) {
                // update textareas
                case 'textarea':
                    element = form.find("textarea[name='" + column.name + "']");
                    // sanitiy checks
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
                    break;
                // update input fields
                case 'input':
                default:
                    element = form.find("input[name='" + column.name + "']");
                    // sanitiy checks
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
            }
        });
        // update sequence item html code with updated data
        datatableSequence.updateSequence(data.sequence, data);
    };

    /*
        Gets data template for new rows.

        Returns:
          array: Datatables row data for a new row.
    */
    this.getDataTemplate = function() {
        var data = {
            mode: "create",
            errors: "",
        };
        // check custom columns for custom initialization values (default: '')
        $.each(datatableSequence.columns, function(index, column) {
            data[column.data] = "";
            if(typeof column.datatableSequence.createValue != "undefined")
                data[column.data] = column.datatableSequence.createValue;
        });
        data.sequence = datatableSequence.newSequence(data);
        return data;
    };

    /*
        Checks, if the edit form is valid.

        Adds error classes to form groups with errors.

        Args:
          form (jQuery node): Node containing the form fields.

        Returns:
          true: If the form is valid.
          false: Otherwise.
    */
    this.editFormValid = function(form) {
        var valid = true;
        // for all columns
        $.each(datatableSequence.columns, function(index, column) {
            // skip, if no error function is defined
            if(typeof column.datatableSequence.createError == "undefined")
                return;
            // set error function for mandatory fields, if only true is given
            if(column.datatableSequence.createError === true)
                column.datatableSequence.createError = function(value) {
                    return value === ""; };
            var element, value, group = false;
            switch(column.datatableSequence.type) {
                // get textarea
                case 'textarea':
                    element = form.find("textarea[name='" + column.name + "']");
                    value = element.val();
                    group = element.closest('.form-group');
                    break;
                // get input field
                case 'input':
                default:
                    element = form.find("input[name='" + column.name + "']");
                    value = element.val();
                    group = element.closest('.form-group');
            }
            // validate fields and set error class on errors
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

    /*
        Adds a row from source to target table.

        Adds rows only in add mode.

        Args:
          rowId (int): Row ID of the row to add.

        Returns:
          false: Prevents link execution.
    */
    this.addRow = function(rowId) {
        // only add rows in add mode
        if(datatableSequence.mode !== 'add')
            return false;
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

    /*
        Removes a row from target table.

        Removes all type of rows in add mode. Removes only the created/edited
        row in create/edit mode, ends then in add mode.

        Args:
          link (jQuery node): Node of the remove link.

        Returns:
          false: Prevents link execution.
    */
    this.removeRow = function(link) {
        // get row node
        var tr = $(link).parents('tr');
        // get row node for links in child rows
        if(tr.hasClass('child'))
            tr = tr.prev('tr');
        // get datatable row
        var row = datatableSequence.target.table.row(tr);
        // remove always, if not in edit mode
        if(datatableSequence.mode == "add") {
            row.remove().draw();
            return false;
        }
        // remove only edited row in create/edit mode
        if(row.child()) {
            row.remove().draw();
            // set add mode
            datatableSequence.mode = "add";
            return false;
        }
        return false;
    };

    /*
        Creates a row in target table and edits it.

        Creates rows only in add mode, ends then in create mode.

        Note:
          Binds enter key to prevent submission of the whole form.

        Returns:
          false: Prevents link execution.
    */
    this.createRow = function() {
        // prevent multiple creations
        if(datatableSequence.mode !== "add")
            return false;
        datatableSequence.mode = "create";
        // set data template and redraw row
        var data = datatableSequence.getDataTemplate();
        var row = datatableSequence.target.table.row.add(data).draw();
        // open edit area
        datatableSequence.editRow($(row.node()));
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

    /*
        Edits a row in target table by opening a child row with the edit form.

        Edits rows in add/create mode. Create mode is retained, add mode ends
        in edit mode.

        See https://datatables.net/reference/api/row().child()

        Args:
          link (jQuery node): Node of the edit link.

        Returns:
          false: Prevents link execution.
    */
    this.editRow = function(link) {
        // prevent multiple edits
        if(datatableSequence.mode == "edit")
            return false;
        // set edit mode on add mode (create mode is retained)
        if(datatableSequence.mode == "add")
            datatableSequence.mode = "edit";
        // get and redraw row
        var row = datatableSequence.target.table.row($(link).closest('tr'))
            .invalidate('data').draw(false);
        // open edit area
        row.child(datatableSequence.target.editDiv(row.data())).show();
        $(row.child()).addClass('child');
        return false;
    };

    /*
        Saves an edited row in target table.

        Saves rows only in create/edit mode, ends in add mode.

        Args:
          link (jQuery node): Node of the save link.

        Returns:
          false: Prevents link execution.
    */
    this.saveRow = function(link) {
        // save only in create/edit mode
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
        // set add mode
        datatableSequence.mode = "add";
        // update and draw row
        row.data(data).draw();
        // close edit area
        row.child.remove();
        return false;
    };

    /*** TEMPLATES ***********************************************************/

    /*
        Template for target table.

        Contains a header, the table and a wrapper for the deform sequence
        serialization.
    */
    this.target.tableNode = function() {
        // header
        var header = datatableSequence.target.header ?
            '<h3 class="datatable_sequence_' + datatableSequence.oid +
                '_target_header"></h3>' : '';
        // table and sequence wrapper
        var html = header +
            '<input type="hidden" name="__start__"' + 
                'value="' + datatableSequence.name + ':sequence" />' +
            '<table id="datatable_sequence_' + datatableSequence.oid + '_target"' +
                'class="table table-hover cs-datatables"></table>' +
            '<input type="hidden" name="__end__"' + 
                'value="' + datatableSequence.name + ':sequence" />';
        return html;
    };

    /* 
        Template for more column of target table.

        Shows a zoom-in icon, if collapsed data is available.
        Shows a "new" label for created rows.

        See https://datatables.net/reference/option/columns.render#function
    */
    this.target.moreCol = function(data, type, row, meta) {
        var table = datatableSequence.target.table;
        // ensure, table is initialized
        if(!table)
            return '';
        // show "new" label for new rows
        if(data.mode === "create")
            return '<i><small>' + table.i18n('custom.new') + '</small></i>';
        // check, if there are collapsed columns with data
        var hasData = false;
        var isVisible = table.columns().responsiveHidden();
        table.row(meta.row).columns().every(function(index) {
            var name = datatableSequence.target.columns[index].name;
            if(!isVisible[index] && data[name])
                hasData = true;
        });
        // show zoom-in icon
        return hasData ? 
            '<span class="more">' +
                '<span class="glyphicon glyphicon-zoom-in"></span>' +
            '</span>' : '';
    };

    /* 
        Template for more div of target table rows.

        Contains a table with all collapsed data presented.

        See https://datatables.net/reference/option/responsive.details.renderer#function
    */
    this.target.moreDiv = function(api, rowIdx, columns) {
        // add collapsed data as table rows
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
        // wrap tables rows with table
        return data ? $('<table class="table"/>').append(data) : false;
    };

    /* 
        Template for controls head of target table rows.

        Contains the create link.
    */
    this.target.controlsHead = function() {
        var table = datatableSequence.target.table;
        // create link
        return  '<a href="#" class="cs-thin"' +
                    'onclick="return deform.datatableSequences.' +
                        datatableSequence.oid + '.createRow();">' +
                    '<span class="glyphicon glyphicon-plus"></span> ' +
                    table.i18n('custom.create') +
                '</a>';
    };

    /* 
        Template for controls column of target table.

        Contains the edit/remove links.

        See https://datatables.net/reference/option/columns.render#function
    */
    this.target.controlsCol = function(data, type, row, meta) {
        var table = datatableSequence.target.table;
        // ensure, table is initialized
        if(!table)
            return '';
        // edit link (only for created/edited rows in add mode)
        if(data.mode !== "add" && datatableSequence.mode === "add")
            return  '<a href="#" onclick="return ' +
                            'deform.datatableSequences.' + datatableSequence.oid +
                            '.editRow(this);" class="edit">' +
                        '<span class="glyphicon glyphicon-pencil"></span> ' +
                        table.i18n('custom.edit') +
                    '</a>';
        // remove link (only for added rows)
        if(data.mode === "add")
            return  '<a href="#" onclick="return ' +
                            'deform.datatableSequences.' + datatableSequence.oid +
                            '.removeRow(this);">' +
                        '<span class="glyphicon glyphicon-minus"></span> ' +
                        table.i18n('custom.remove') +
                    '</a>';
        return '';
    };

    /*
        Template for edit div of target table rows.

        Contains the edit form and apply/remove buttons.
    */
    this.target.editDiv = function(data) {
        var table = datatableSequence.target.table;
        var inputs = "";
        // if a custom createForm function is provided, use it
        if(datatableSequence.createForm)
            inputs += datatableSequence.createForm(data);
        // otherwise add default templates for form fields
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
                                'value="' + (data ? data[column.name] : '') + '">' +
                        '</div>';
            });
        // buttons
        var buttons = '' +
            // apply button
            '<a href="#" class="cs-datatables-apply" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'saveRow(this);">' +
                '<button class="btn btn-info">' +
                    table.i18n('custom.apply') +
                '</button>' +
            '</a> ' +
            // remove button
            '<a href="#" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'removeRow(this);">' +
                '<button class="btn btn-danger">' +
                    table.i18n('custom.remove') +
                '</button>' +
            '</a>';
        return $('<div class="cs-datatables-edit"/>').append(inputs + buttons);
    };

    /* 
        Template for show column of target table.

        Contains the data of the created rows and the error messages.
        Should be displayed in the first main column for responsiveness.
        Data could contain invisible columns, which are only displayed here.

        See https://datatables.net/reference/option/columns.render#function
        See https://datatables.net/manual/data/orthogonal-data
    */
    this.target.showCol = function(data, type, row, meta) {
        // orthogonal data for display
        if(type !== 'display' && type !== 'filter')
            return data;
        // show template only for created/edited rows
        if(row.mode === "add")
            return data;
        var html = "";
        // add column data
        $.each(datatableSequence.columns, function(index, column) {
            // if column should be displayed and contains data
            if(column.datatableSequence.createShow && row[column.name])
                html += '<small>' + column.title + ':</small> ' +
                        datatableSequence.escape(row[column.name]) + "<br>";
        });
        // add error messages
        return html + row.errors;
    };

    /* 
        Template for mode column of target table.

        Used for custom sort order to make created rows sticky.

        See https://datatables.net/reference/option/columns.render#function
        See https://datatables.net/manual/data/orthogonal-data
    */
    this.target.modeCol = function(data, type, row, meta) {
        // orthogonal data for display
        if(type === 'sort') {
            switch(data) {
                case 'create':
                    return 1;
                case 'edit':
                    return 2;
                case 'add':
                    return 3;
                default:
                    return data;
            }
        }
        return data;
    };

    /*
        Template for source table.

        Contains a header, the table and a footer for individual column search.
    */
    this.source.tableNode = function() {
        // header
        var header = datatableSequence.source.header ?
            '<h3 class="datatable_sequence_' + datatableSequence.oid +
                '_source_header"></h3>' : '';
        // footer
        var footer = '<tfoot>';
        var search = false;
        $.each(datatableSequence.source.columns, function(index, column) {
            // add search field, if it should be displayed
            search = column.datatableSequence &&
                     column.datatableSequence.footerSearch === true;
            footer += search ?
                '<th class="multifilter">' + column.title + '</th>' :
                '<th></th>';
        });
        footer += '</tfoot>';
        // table
        var html = header +
            '<div class="container-fluid">' +
                '<table id="datatable_sequence_' + datatableSequence.oid + '_source"' +
                        'class="table table-hover cs-datatables">' +
                    footer +
                '</table>' +
            '</div>';
        return html;
    };

    /* 
        Template for more column of source table.

        Shows a zoom-in icon, if collapsed data is available.

        See https://datatables.net/reference/option/columns.render#function
    */
    this.source.moreCol = function(data, type, row, meta) {
        var table = datatableSequence.source.table;
        // ensure, table is initialized
        if(!table)
            return '';
        // check, if there are collapsed columns with data
        var isVisible = table.columns().responsiveHidden();
        var hasData = false;
        table.row(meta.row).columns().every(function(index) {
            var name = datatableSequence.source.columns[index].name;
            if(!isVisible[index] && data[name])
                hasData = true;
        });
        // show zoom-in icon
        return hasData ? 
            '<span class="more">' +
                '<span class="glyphicon glyphicon-zoom-in"></span>' +
            '</span>' : '';
    };

    /* 
        Template for more div (for collapsed data) of source table rows.

        See this.target.moreDiv
    */
    this.source.moreDiv = this.target.moreDiv;

    /* 
        Template for controls column of source table.

        Contains the add link.

        See https://datatables.net/reference/option/columns.render#function
    */
    this.source.controlsCol = function(data, type, row, meta) {
        var table = datatableSequence.source.table;
        // add link
        return table ?
            '<a href="#" onclick="return ' +
                    'deform.datatableSequences.' + datatableSequence.oid + '.' +
                    'addRow(' + meta.row + ');">' +
                '<span class="glyphicon glyphicon-plus"></span> ' +
                table.i18n('custom.add') +
            '</a>' : '';
    };

    /*** EVENTS **************************************************************/

    /*
        Redraws the table after changing a bootstrap navigation tab.

        Binds to the bootstrap navigation tabs.
        Fixes the table width.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.redraw = function(obj) {
        $("a[data-toggle=\"tab\"]").on("shown.bs.tab", function (e) {
            obj.table.columns.adjust();
        });
    };

    /*
        Opens and closes the details.

        Binds to the more column on click event.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.more = function(obj) {
        $("#" + obj.tableId + ' tbody').on('click', 'td.more', function() {
            var row = obj.table.row($(this).closest('tr'));
            var data = row.data();
            // show nothing for created rows
            if(data.mode == "create")
                return;
            // check, if there are collapsed columns with data
            var isVisible = row.columns().responsiveHidden();
            var hasData = false;
            row.columns().every(function(index) {
                var name = obj.columns[index].name;
                if(!isVisible[index] && data[name])
                    hasData = true;
            });
            // return, if there are no details
            if(!hasData)
                return;
            // show zoom-out icon if details are opened
            if(row.child.isShown()) {
                row.child().show();
                $(this).html(
                    '<span class="glyphicon glyphicon-zoom-out" ' +
                        'aria-hidden="true"></span>'
                );
            // show zoom-in icon if details are collapsed
            } else {
                row.child(true);
                $(this).html(
                    '<span class="glyphicon glyphicon-zoom-in" ' +
                        ' aria-hidden="true"></span>'
                );
            }
        });
    };

    /*
        Initializes the column search.

        Binds to individual column search input fields.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.search = function(obj) {
        // set placeholder
        $("#" + obj.tableId + ' tfoot th.multifilter').each(function () {
            var text = obj.table.i18n( 'custom.search' ) + " " + $(this).text();
            $(this).html('<input type="text" placeholder="' + text + '" />');
        });
        // bind keyup to search updates
        obj.table.columns().every(function () {
            var that = this;
            $('input', this.footer()).on('keyup change', function() {
                if (that.search() !== this.value) {
                    that.search( this.value ).draw();
                }
            });
        });
    };

    /*
        Applies all open edit forms before submitting the form.

        Binds to form on submit.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.save = function(obj) {
        $("#" + obj.tableId).closest("form").on('submit', function(){
            $(obj.table.table().node()).find("a.cs-datatables-apply").click();
        });
    };

    /*
        Sets the header for the table.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.setHeader = function(obj) {
        if(obj.header !== "")
            $('.' + obj.tableId + '_header').first().html(
                obj.table.i18n(obj.header));
        else
            $('.' + obj.tableId + '_header').remove();
    };

    /*
        Sets the text for the create icon.

        Sets the text after init of the tables for i18n.

        Args:
          obj (this.target|this.source): Datatable meta object.
    */
    this.events.setCreateText = function(obj) {
        // find column index of controls column
        var controlsIndex = false;
        $.each(obj.columns, function(index, column) {
            if(column.name === "controls")
                controlsIndex = index;
        });
        // set create icon text
        var header = $(obj.table.columns(controlsIndex).header());
        header.html(datatableSequence.target.controlsHead());
    };

    /*** COLUMS **************************************************************/

    /*
        Sets the target colums.

        Columns:
        - more: zoom-in/out icon to show details, if available
        - controls: control links (edit, remove)
        - sequence: contains html code for colander sequence item
        - mode: add|create|edit
        - errors: error feedback from colander validation
    */
    this.target.columns = (function() {
        var customCols = $.extend(true, {}, datatableSequence.getSortedColumns());
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
                name: "controls",
                data: null,
                className: "text-left nowrap all",
                width: "80px",
                orderable: false,
                searchable: false,
                render: datatableSequence.target.controlsCol
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
                render: datatableSequence.target.modeCol
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

    /*
        Sets the source colums.

        Columns:
        - more: zoom-in/out icon to show details, if available
        - controls: control links (add)
    */
    this.source.columns = (function() {
        var customCols = $.extend(true, {}, datatableSequence.getSortedColumns());
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
                name: "controls",
                data: null,
                width: "80px",
                className: "text-right nowrap all",
                orderable: false,
                searchable: false,
                render: datatableSequence.source.controlsCol
            },
            customCols.collapsed,
            customCols.invisible,
        ].flat();
    })();

    /*** INIT ****************************************************************/

    /*
        Initializes the datatable sequence.
    */
    this.init = function() {

        // initialization
        $(document).ready(function() {

            // generate html
            var htmlNode = ".datatable_sequence_" + datatableSequence.oid;
            $(htmlNode).append(datatableSequence.target.tableNode());
            $(htmlNode).append(datatableSequence.source.tableNode());

            // find column index of mode column
            var modeIndex = false;
            $.each(datatableSequence.target.columns, function(index, column) {
                if(column.name === "mode")
                    modeIndex = index;
            });
            
            // initialize target table
            datatableSequence.target.table = $(
                "#" + datatableSequence.target.tableId).DataTable({
                data: $(".datatable_sequence_" + datatableSequence.oid).data('rows'),
                language: $(".datatable_sequence_" + datatableSequence.oid).data('lang'),
                paging: false,
                info: false,
                searching: false,
                autoWidth: false,
                fixedHeader: false,
                responsive: {
                    details: {
                        renderer: datatableSequence.target.moreDiv,
                        type: 'column'
                    }
                },
                columns: datatableSequence.target.columns,
                order: [
                    [ modeIndex, "asc" ],  // create rows at the top
                    [ 1, "asc" ]           // first displayed row
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
                fixedHeader: false,
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
