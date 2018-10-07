// dependancies
if(typeof deform == "undefined")
    throw new Error("'deform' is not included yet. exiting.");
// registry
if(typeof deform.datatableSequences == "undefined")
    deform.datatableSequences = {};

/*
    Deform Datatables Widget

    This class aids the integration of jquery datatables and deform sequences.
    It generates two datatables: One target table with the current sequence
    (one row is one sequence item) and one source table (ajax datasource) with
    rows to add to the sequence. The serialized sequece item for colander is
    saved into a row cell of the target table. Additionally new sequence items
    might be created and edited.
    
    Initialization:
    
        <div class="datatable_sequence_${oid}"
            data-rows="${rows}" data-lang="${lang}"></div>
        
        <script>
            var ds = new deform.DatatableSequence({
                oid: "${oid}",
                name: "${name}",
                title: "${title}",
                minLen: "${min_len}",
                maxLen: "${max_len}",
                nowLen: "${now_len}",
                proto: "${prototype}",
                api: "${api}/<PATH>",
                unique: "<COLUMNNAME>" | function(data) -> true if unique,
                columns: [<DATATABLECOLUMNS>],
            }).init();
        </script>

    Additional column attributes for custom columns:

        ds: {
            position:     "displayed" | "collapsed" | "invisible"
            type:         "input" | "textarea" (default: "input")
            createValue:  string (default: "")
            createForm:   true | false (default: false)
            createShow:   true | false (default: false, shows field in table]
            createError:  true (mandantory) | function(value) -> true on error
            footerSearch: true | false (creates footer search field)
        }

    Functional columns:
    
        target table
        - more: zoom-in/out icon to show details, if available
        - controls: control links (edit, remove)
        - sequence: contains html code for colander sequence item
        - mode: add|create|edit
        - errors: error feedback from colander validation

        source table
        - more: zoom-in/out icon to show details, if available
        - controls: control links (add)

    TODO:
    - orderable rows
    - min/max rows
    - this.templates.edit: switch for input types (input, textarea, etc.)
    - layover for edit rows?
    - layover for add row?
    - highlighting of edit div on clicks on deactivated controls?
*/

var DatatableSequence = function(vars) {

    // self reference
    var ds = this;

    // self in registry
    this.registry = "deform.datatableSequences." + vars.oid;

    /**************************************************************************
        VARIABLES
    **************************************************************************/

    // deform
    this.oid = vars.oid;
    this.name = vars.name;
    this.title = vars.title;
    this.minLen = parseInt(vars.minLen);
    this.maxLen = parseInt(vars.maxLen);
    this.nowLen = parseInt(vars.nowLen);
    this.orderable = (vars.orderable ? parseInt(vars.orderable) == 1 : false);
    this.proto = vars.proto;
    this.api = vars.api;

    // selectors
    var base = "datatable_sequence_" + ds.oid;
    this.sel = {
        base:         base,
        html:         "." + base,
        targetTable:  "#" + base + "_target",
        targetArea:   "." + base + "_target_area",
        sourceTable:  "#" + base + "_source",
        sourceArea:   "." + base + "_source_area",
        sourceFilter: "#" + base + "_source_filter",
        controls:     "." + base + "_controls",
        modalAdd:     "#" + base + "_modal_add",
        modalCreate:  "#" + base + "_modal_create",
    };

    // datatable
    this.language = $(ds.sel.html).data('language');
    this.mode = "add";                  // "add" | "create" | "edit"
    this.columns = vars.columns;        // custom datatable columns
    this.createForm = vars.createForm;  // create form for new rows
    this.unique = vars.unique;          // string (id column for unique rows) |
                                        // function(data) -> true if unique


    /**************************************************************************
        TEMPLATES
    **************************************************************************/

    this.templates = {

        /**
         * Main template for the datatable sequence.
         */
        datatableSequence: function() {
            var t = ds.templates;            
            return '' +
                t.targetTable() +
                t.controls() +
                t.modal('add', ds.title, t.sourceTable()) +
                t.modal('create', ds.title, t.edit());
        },

        /**
         * Template for modals.
         */
        modal: function(role, title, content, footer) {
            var id = ds.sel.base + '_modal_' + role;
            var close = '' +
                '<button type="button" class="close"' +
                        'data-dismiss="modal" aria-label="Close">' +
                    '<span class="glyphicon glyphicon-remove"></span>' +
                '</button>';
            var pin = role === 'add' ?
                '<button type="button" class="close pin" aria-label="Pin"' +
                        'onclick="return ' + ds.registry + '.pinModal(this);">' +
                    '<span class="glyphicon glyphicon-pushpin"></span>' +
                '</button> ' : '';
            var head =  '<div class="modal-header cs-modal-header">' +
                            close + pin +
                            '<h4 class="modal-title" id="' + id + '_label">' +
                                title +
                            '</h4>' + 
                        '</div>';
            var body = '<div class="modal-body">' + content + '</div>';
            var foot = footer ? 
                '<div class="modal-footer">' + footer + '</div>' : '';
            return '' +
                '<div class="modal fade cs-modal" id="' + id + '" tabindex="-1" ' +
                        'role="dialog" aria-labelledby="' + id + '_label">' +
                    '<div class="modal-dialog modal-lg" role="document">' +
                        '<div class="modal-content">' +
                             head + body + foot +
                        '</div>' +
                    '</div>' +
                '</div>';
        },

        /**
         * Template for control buttons (add/create).
         */
        controls: function() {
            return '' +
                '<div class="btn-group" role="group" ' +
                        'class="' + ds.sel.base + '_controls" ' +
                        'aria-label="' + ds.sel.base + '_controls">' +
                    '<button type="button" class="btn btn-default"' +
                            'data-toggle="modal" ' + 
                            'data-target="' + ds.sel.modalAdd + '">' +
                        ds.language.custom.add +
                    '</button>' +
                    '<button type="button" class="btn btn-default"' +
                            'data-toggle="modal" ' + 
                            'data-target="' + ds.sel.modalCreate + '">' +
                        ds.language.custom.create +
                    '</button>' +
                '</div>';
        },

        /**
         * Template for target table.
         * 
         * Contains the table and a wrapper for deform sequence serialization.
         */
        targetTable: function() {
            // table and sequence wrapper
            var html = '' +
                '<input type="hidden" name="__start__"' + 
                    'value="' + ds.name + ':sequence" />' +
                '<table id="' + ds.sel.base + '_target"' +
                    'class="table table-hover cs-datatables"></table>' +
                '<input type="hidden" name="__end__"' + 
                    'value="' + ds.name + ':sequence" />';
            // area
            var area = '' + 
                '<div class="' + ds.sel.base + '_target_area"/>';
            return $(area).append(html).html();
        },

        /** 
         * Template for more column of target table.
         * 
         * Shows a zoom-in icon, if collapsed data is available.
         * Shows a "new" label for created rows.
         * 
         * See https://datatables.net/reference/option/columns.render#function
         */
        targetColumnMore: function(data, type, row, meta) {
            var table = ds.target.table;
            // ensure, table is initialized
            if(!table)
                return '';
            // show "new" label for new rows
            if(data.mode === "create")
                return '<i><small>' + ds.language.custom.new +
                    '</small></i>';
            // show zoom-in icon, if there are hidden details
            return ds.dataHidden(table.row(meta.row)) ? 
                '<span class="more">' +
                    '<span class="glyphicon glyphicon-zoom-in"></span>' +
                '</span>' : '';
        },

        /** 
         * Template for more div of target table rows.
         * 
         * Contains a table with all collapsed data presented.
         * 
         * See https://datatables.net/reference/option/responsive.details.renderer#function
         */
        more: function(api, rowIdx, columns) {
            // add collapsed data as table rows
            var data = jQuery.map(columns, function(column, index) {
                var settings = api.settings();
                console.log(settings);
                if(!column.data)
                    return '';
                return column.hidden ?
                    '<tr data-dt-row="' + column.rowIndex + '" data-dt-column="' + 
                            column.columnIndex + '">' +
                        '<td><small>' + column.title + ':' + '<small></td> ' +
                        '<td class="fullwidth">' + column.data + '</td>'+
                    '</tr>' : '';
            }).join('');
            // wrap tables rows with table
            return data ? $('<table class="table cs-datatables-row-details"/>')
                .append(data) : false;
        },

        /** 
         * Template for controls column of target table.
         * 
         * Contains the edit/remove buttons.
         * 
         * See https://datatables.net/reference/option/columns.render#function
         */
        targetColumnControls: function(data, type, row, meta) {
            // edit button
            var edit = '' +
                '<a href="#" class="btn btn-default btn-sm" role="button" ' +
                        'onclick="return ' + ds.registry + '.editRow(this);" >' +
                    ds.language.custom.edit +
                '</a>';
            // remove button
            var remove = '' +
                '<a href="#" class="btn btn-default btn-sm" role="button" ' +
                        'onclick="return ' + ds.registry + '.removeRow(this);">' +
                    ds.language.custom.remove +
                '</a>';
            // edit button only for created/edited rows in add mode
            var buttons = '';
            if(data.mode !== "add" && ds.mode === "add")
                buttons += edit;
            // remove button always
            buttons += remove;
            return '' +
                '<div class="btn-group-vertical cs-row-controls" role="group">' +
                    buttons +
                '</div>';
        },

        /**
         * Template for edit div of target table rows.
         * 
         * Contains the edit form and apply/remove buttons.
         */
        edit: function(data) {
            var inputs = "";
            // if a custom createForm function is provided, use it
            if(ds.createForm)
                inputs += ds.createForm(data);
            // otherwise add default templates for form fields
            else
                $.each(ds.columns, function(index, column) {
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
                '<a href="#" class="cs-datatables-apply" ' +
                        'onclick="return ' + ds.registry + '.saveRow(this);">' +
                    '<button class="btn btn-info">' +
                        ds.language.custom.apply +
                    '</button>' +
                '</a> ' +
                // remove button
                '<a href="#" onclick="return ' + ds.registry + '.removeRow(this);">' +
                    '<button class="btn btn-danger">' +
                        ds.language.custom.remove +
                    '</button>' +
                '</a>';
            return '' +
                '<div class="cs-datatables-edit">' +
                    inputs + buttons +
                '</div>';
        },

        /** 
         * Template for show column of target table.
         * 
         * Contains the data of the created rows and the error messages.
         * Should be displayed in the first main column for responsiveness.
         * Data could contain invisible columns, which are only displayed here.
         * 
         * See https://datatables.net/reference/option/columns.render#function
         * See https://datatables.net/manual/data/orthogonal-data
         */
        targetColumnShow: function(data, type, row, meta) {
            // orthogonal data for display
            if(type !== 'display')
                return data;
            // show template only for created/edited rows
            if(row.mode === "add")
                return data;
            var html = "";
            // add column data
            $.each(ds.columns, function(index, column) {
                // if column should be displayed and contains data
                if(column.datatableSequence.createShow && row[column.name])
                    html += '<small>' + column.title + ':</small> ' +
                            ds.escape(row[column.name]) + "<br>";
            });
            // add error messages
            return html + row.errors;
        },

        /** 
         * Template for mode column of target table.
         * 
         * Used for custom sort order:
         * 1. created rows
         * 2. editable rows
         * 3. added rows
         * 
         * See https://datatables.net/reference/option/columns.render#function
         * See https://datatables.net/manual/data/orthogonal-data
         */
        targetColumnMode: function(data, type, row, meta) {
            // orthogonal data for sort
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
        },

        /**
         * Template for source table.
         * 
         * Contains the table and a footer for individual column search.
         */
        sourceTable: function() {
            // footer
            var footer = '<tfoot>';
            var search = false;
            $.each(ds.source.columns, function(index, column) {
                // add search field, if it should be displayed
                search = column.datatableSequence &&
                         column.datatableSequence.footerSearch === true;
                footer += search ?
                    '<th class="multifilter">' + 
                        '<input type="text" placeholder="' +
                            ds.language.custom.search + ' ' +
                            column.title + '" />' +
                    '</th>' : '<th></th>';
            });
            footer += '</tfoot>';
            // table
            var html = '' +
                '<div class="container-fluid">' +
                    '<table id="' + ds.sel.base + '_source"' +
                            'class="table table-hover cs-datatables">' +
                        footer +
                    '</table>' +
                '</div>';
            // modal
            var area = '' +
                '<div class="' + ds.sel.base + '_source_area"/>';
            return $(area).append(html).html();
        },

        /** 
         * Template for more column of source table.
         * 
         * Shows a zoom-in icon, if collapsed data is available.
         * 
         * See https://datatables.net/reference/option/columns.render#function
         */
        sourceColumnMore: function(data, type, row, meta) {
            var table = ds.source.table;
            // ensure, table is initialized
            if(!table)
                return '';
            // show zoom-in icon, if there are hidden details
            return ds.dataHidden(table.row(meta.row)) ? 
                '<span class="more">' +
                    '<span class="glyphicon glyphicon-zoom-in"></span>' +
                '</span>' : '';
        },

        /* 
         * Template for controls column of source table.
         * 
         * Contains the add link.
         * 
         * See https://datatables.net/reference/option/columns.render#function
         */
        sourceColumnControls: function(data, type, row, meta) {
            var table = ds.target.table;
            // ensure, table is initialized
            if(!table)
                return '';
            // add button
            var add = '' +
                '<a href="#" class="btn btn-default btn-sm" role="button" ' +
                        'onclick="return ' + ds.registry + 
                        '.addRow(' + meta.row + ');" >' +
                    ds.language.custom.add +
                '</a>';
            // remove button
            var added = ds.rowAdded(row);
            var remove = added ?
                '<a href="#" class="btn btn-default btn-sm" role="button" ' +
                        'onclick="return ' + ds.registry + 
                        '.removeRow(' + added.index() + ');">' +
                    ds.language.custom.remove +
                '</a>' : '';
            // remove button if added, add button otherwise
            buttons = added ? remove : add;
            return '' +
                '<div class="btn-group-vertical cs-row-controls" role="group">' +
                    buttons +
                '</div>';
        },

    };


    /**************************************************************************
        EVENTS
    **************************************************************************/

    this.events = {

        /*
            Redraws the table after changing a bootstrap navigation tab.

            Binds to the bootstrap navigation tabs.
            Fixes the table width.

            Args:
              obj (this.target|this.source): Datatable meta object.
        */
        redraw: function(obj) {
            $("a[data-toggle=\"tab\"]").on("shown.bs.tab", function (e) {
                obj.table.columns.adjust();
            });
        },

        /*
            Opens and closes the details.

            Binds to the more column on click event.

            Args:
              obj (this.target|this.source): Datatable meta object.
        */
        more: function(obj) {
            $(obj.tableId + ' tbody').on('click', 'td.more', function() {
                var row = obj.table.row($(this).closest('tr'));
                var data = row.data();
                // show nothing for created rows
                if(data.mode == "create")
                    return;
                // return, if there are no details
                if(!ds.dataHidden(row))
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
        },

        /*
            Initializes the column search.

            Binds to individual column search input fields.

            Args:
              obj (this.target|this.source): Datatable meta object.
        */
        search: function(obj) {
            // bind keyup to search updates
            obj.table.columns().every(function () {
                var that = this;
                $('input', this.footer()).on('keyup change', function() {
                    if (that.search() !== this.value) {
                        that.search( this.value ).draw();
                    }
                });
            });
        },

        /*
            Applies all open edit forms before submitting the form.

            Binds to form on submit.

            Args:
              obj (this.target|this.source): Datatable meta object.
        */
        save: function(obj) {
            $(obj.tableId).closest("form").on('submit', function(){
                $(obj.table.table().node()).find("a.cs-datatables-apply").click();
            });
        },

        /*
            Resets search forms, when modal is closed and not pinned

            Args:
              obj (this.target|this.source): Datatable meta object.
        */
        closeReset: function(obj) {
            $(ds.sel.modalAdd).on('hidden.bs.modal', function (e) {
                // consider pin
                if($(ds.sel.modalAdd + ' .pin').hasClass('pinned'))
                    return;
                // reset individual search fields
                obj.table.columns().every(function () {
                    var footer = $('input', this.footer()).val('').change();
                });
                // reset main search field
                obj.table.search('');
                //redraw
                obj.table.draw();
            });
        },

    };

    /**************************************************************************
        TABLES
    **************************************************************************/

    this.target = {
        // datatable table
        table: false,
        // table html node selector
        tableId: ds.sel.targetTable,
        // events to bind (bound on initialization)
        events: ['more', 'save', 'redraw'],
        // initial data
        data: $(ds.sel.html).data('data'),
        // columns of target table
        columns: (function() {
            // clone custom columns
            var customCols = $.extend(true, {}, ds.getSortedColumns());
            // show created row data in first custom column
            customCols.displayed[0].render = ds.templates.targetColumnShow;
            return [
                {
                    name: "more",
                    data: null,
                    className: "text-center all more",
                    width: "30px",
                    orderable: false,
                    searchable: false,
                    render: ds.templates.targetColumnMore
                },
                customCols.displayed,
                {
                    name: "controls",
                    data: null,
                    className: "text-right nowrap all",
                    orderable: false,
                    searchable: false,
                    render: ds.templates.targetColumnControls
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
                    render: ds.templates.targetColumnMode
                },
                {
                    name: "errors",
                    data: "errors",
                    visible: false,
                    orderable: false,
                    searchable: false,
                }
            ].flat();
        })(),
    };
    
    // source table meta object
    this.source = {
        // datatable table
        table: false,
        // table html node selector
        tableId: ds.sel.sourceTable,
        // events to bind (bound on initialization)
        events: ['more', 'search', 'closeReset', 'redraw'],
        // columns of target table
        columns: (function() {
            var customCols = $.extend(true, {}, ds.getSortedColumns());
            return [
                {
                    name: "more",
                    data: null,
                    className: "text-center all more",
                    width: "30px",
                    orderable: false,
                    searchable: false,
                    render: ds.templates.sourceColumnMore
                },
                customCols.displayed,
                {
                    name: "controls",
                    data: null,
                    className: "text-right nowrap all",
                    orderable: false,
                    searchable: false,
                    render: ds.templates.sourceColumnControls
                },
                customCols.collapsed,
                customCols.invisible,
            ].flat();
        })()
    };

};


DatatableSequence.prototype = {

    /************************************************************************** 
        AUXILIARY 
    **************************************************************************/

    /** 
     * Escapes html characters for display.
     *
     * Args:
     *   str (string): Unescaped string.
     *
     * Returns:
     *   string: Escaped string.
     */
    escape: function(str) {
        return jQuery('<div />').text(str).html();
    },

    /** 
     * Generates html code for the data of a new sequence item.
     *
     * If data is provided, the sequence gets updated.
     *
     * Note:
     *   This function is based on addSequence() in deform.js
     *
     * Args:
     *   data (array, optional): Datatables row data.
     *
     * Returns:
     *   string: Html code for serialized sequence item data.
     */
    newSequence: function(data) {
        var ds = this;
        var fieldmatch = /deformField(\d+)/;
        var namematch = /(.+)?-[#]{3}/;
        var html = decodeURIComponent(ds.proto);
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
            ds.updateSequence($htmlnode, data);

        return $htmlnode.prop('outerHTML');
    },

    /**
     * Checks, if a row already added.
     *
     * Args:
     *   data (array): Datatables row data.
     *
     * Returns:
     *   Datatables row: If row is already added.
     *   false: Otherwise.
     */
    rowAdded: function(data) {
        var ds = this;
        switch(typeof ds.unique) {
            // the column name is provided as a string
            case 'string':
                var id = ds.unique;
                var row = false;
                ds.target.table.rows().every(function() {
                    if(this.data()[id] == data[id])
                        row = this;
                });
                return row;
            // a custom function for the data is provided
            case 'function':
                return ds.unique(data);
            default:
                // TODO: compare all columns as default
                return false;
        }
    },

    /**
     * Gets custom columns sorted by position.
     *
     * Custom columns are the columns provided by the user as init parameter.
     * They are merged with other functional columns on initialization. The
     * positions denote the slots, where they should be included.
     *
     * The positions are:
     *   - displayed: Visible main columns
     *   - collapsed: Collapsed columns, visible by clicking the more column
     *   - invisible: Invisible columns used for hidden data
     *   
     * Returns:
     *   dictionary: {
     *     'displayed': array of displayed columns,
     *     'collapsed': array of collapsed columns,
     *     'invisible': array of invisible columns
     *   }
     */
    getSortedColumns: function() {
        var ds = this;
        var cols = {};
        $.each(['displayed', 'collapsed', 'invisible'], function(index, value) {
            cols[value] = $.grep(ds.columns, function(n, i) {
                return n.datatableSequence.position == value;
            });
        });
        return cols;
    },

    /**
     * Updates sequence item html code with row data.
     *
     * Args:
     *   sequence (jQuery node): Node containing the sequence item html code.
     *   sequence (string): Html code for sequence item data.
     *   data (array): Datatables row data.
     */
    updateSequence: function(sequence, data) {
        var ds = this;
        // parse string if sequence is not a jquery node object
        if(!(sequence instanceof jQuery))
            sequence = $($.parseHTML(sequence));
        // update mode
        sequence.find("input[name='mode']").val(data.mode);
        // update data columns
        $.each(ds.columns, function(index, column) {
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
    },

    /**
     * Updates row data and sequence item html code with edit form data.
     * 
     * Args:
     *   data (array): Datatables row data.
     *   form (jQuery node): Node containing the form fields
     */
    updateData: function(data, form) {
        var ds = this;
        data.errors = "";
        // update data columns
        $.each(ds.columns, function(index, column) {
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
        ds.updateSequence(data.sequence, data);
    },

    /**
     * Gets data template for new rows.
     *
     * Returns:
     *   array: Datatables row data for a new row.
     */
    getDataTemplate: function() {
        var ds = this;
        var data = {
            mode: "create",
            errors: "",
        };
        // check custom columns for custom initialization values (default: '')
        $.each(ds.columns, function(index, column) {
            data[column.data] = "";
            if(typeof column.datatableSequence.createValue != "undefined")
                data[column.data] = column.datatableSequence.createValue;
        });
        data.sequence = ds.newSequence(data);
        return data;
    },

    /**
     * Checks, if the edit form is valid.
     * 
     * Adds error classes to form groups with errors.
     * 
     * Args:
     *   form (jQuery node): Node containing the form fields.
     * 
     * Returns:
     *   true: If the form is valid.
     *   false: Otherwise.
     */
    editFormValid: function(form) {
        var ds = this;
        var valid = true;
        // for all columns
        $.each(ds.columns, function(index, column) {
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
    },

    /**
     * Checks, if a row has any hidden data.
     * 
     * Args:
     *   row (Datatables row): Row to check for hidden data.
     * 
     * Returns:
     *   true: If the row has hidden data.
     *   false: Otherwise.
     */
    dataHidden: function(row) {
        var isVisible = row.table().columns().responsiveHidden();
        var hasData = false;
        row.columns().every(function(index) {            
            if(!isVisible[index] && row.cell(row.index(), index).data())
                hasData = true;
        });
        return hasData;
    },

    /**
     * Gets the index of the column with a certain name.
     * 
     * Args:
     *   table (meta obj): Table, in which to search.
     *   name (string): Name to search for.
     * 
     * Returns:
     *   int: The index of the found column.
     *   false: If no columns was found.
     */
    getColumnIndex: function(table, name) {
        var colIndex = false;
        $.each(table.columns, function(index, column) {
            if(column.name === name)
                colIndex = index;
        });
        return colIndex;
    },


    /**************************************************************************
        ACTIONS
    **************************************************************************/

    /*
     * Initializes the datatable sequence.
     *
     * - Generates html code
     * - Initializes the target table
     * - Initializes the source table
     * - Bind the events
     * - Adds the instance to the datatableSequence registry
     */
    init: function() {
        var ds = this;
        $(document).ready(function() {

            // generate html
            $(ds.sel.html).append(ds.templates.datatableSequence());

            // initialize target table
            ds.target.table = $(ds.sel.targetTable).DataTable({
                data: ds.target.data,
                language: ds.language,
                paging: false,
                info: false,
                searching: false,
                autoWidth: false,
                fixedHeader: false,
                responsive: {
                    details: {
                        renderer: ds.templates.more,
                        type: 'column'
                    }
                },
                columns: ds.target.columns,
                order: [
                    [ ds.getColumnIndex(ds.target, 'mode'), "asc" ],
                    [ 1, "asc" ]  // first displayed row
                ]
            });
            
            // initialize source table
            ds.source.table = $(ds.sel.sourceTable).DataTable({
                language: ds.language,
                processing: true,
                serverSide: true,
                searchDelay: 600,
                autoWidth: false,
                fixedHeader: false,
                ajax: {
                    type: "POST",
                    contentType: "application/json; charset=utf-8",
                    url: ds.api,
                    xhrFields: {withCredentials: true},
                    dataType: "json",
                    data: function(args) {
                        args.group = false;
                        return JSON.stringify(args);
                    }
                },
                responsive: {
                    details: {
                        renderer: ds.templates.more,
                        type: 'column'
                    }
                },
                columns: ds.source.columns,
                order: [
                    [ 1, "asc" ]  // first displayed row
                ]
            });

            // redraw (to display zoom icon in more column)
            ds.target.table.rows().invalidate('data').draw(false);

            // add events
            $.each([ds.source, ds.target],
                function(_, obj) {
                $.each(obj.events, function(_, event) {
                    ds.events[event](obj);
                });
            });

            // add datatable sequence to registry (for global access)
            deform.datatableSequences[ds.oid] = ds;

        });
    },

    /**
     * Adds a row from source to target table.
     * 
     * Adds rows only in add mode.
     * 
     * Args:
     *   rowId (int): Row ID of the row to add.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    addRow: function(rowId) {
        var ds = this;
        // only add rows in add mode
        if(ds.mode !== 'add')
            return false;
        // get data
        var data = ds.source.table.row(rowId).data();
        // prevent multiple addition
        if(ds.rowAdded(data))
            return false;
        // set data
        data.mode = "add";
        data.errors = "";
        data.sequence = ds.newSequence(data);
        // update table data
        ds.target.table.row.add(data).draw();
        // close modal, if not pinned
        var pin = $(ds.sel.modalAdd + ' .pin').first();
        if(!pin || !pin.hasClass('pinned'))
            $(ds.sel.modalAdd).modal('hide');
        // redraw source table (to update controls)
        ds.source.table.draw(false);
        return false;
    },

    /**
     * Removes a row from target table.
     * 
     * Removes all type of rows in add mode. Removes only the created/edited
     * row in create/edit mode, ends then in add mode.
     * 
     * Args:
     *   obj (node): Node of the remove link.
     *   obj (int): Index of row html node to remove.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    removeRow: function(obj) {
        var ds = this;
        // get row
        var row = false;
        if(typeof obj === "number")         // for indexes
            row = ds.target.table.row(obj);
        else {
            tr = $(obj);
            if(!tr.is('tr'))                // for links
                tr = tr.parents('tr');
            if(tr.hasClass('child'))        // for children
                tr = tr.prev('tr');
            row = ds.target.table.row(tr);
        }
        var remove = false;
        // remove always, if not in edit mode
        if(ds.mode == "add")
            remove = true;
        // remove only edited row in create/edit mode
        if(row.child()) {
            remove = true;
            ds.mode = "add";
        }
        // remove row
        if(!remove)
            return false;
        row.remove().draw();
        // close modal, if not pinned
        var pin = $(ds.sel.modalAdd + ' .pin').first();
        if(!pin || !pin.hasClass('pinned'))
            $(ds.sel.modalAdd).modal('hide');
        // redraw source table (to update controls)
        ds.source.table.draw(false);
        return false;
    },

    /**
     * Creates a row in target table and edits it.
     * 
     * Creates rows only in add mode, ends then in create mode.
     * 
     * Note:
     *   Binds enter key to prevent submission of the whole form.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    createRow: function() {
        var ds = this;
        // prevent multiple creations
        if(ds.mode !== "add")
            return false;
        ds.mode = "create";
        // set data template and redraw row
        var data = ds.getDataTemplate();
        var row = ds.target.table.row.add(data).draw();
        // open edit area
        ds.editRow($(row.node()));
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
    },

    /**
     * Edits a row in target table by opening a child row with the edit form.
     * 
     * Edits rows in add/create mode. Create mode is retained, add mode ends
     * in edit mode.
     * 
     * See https://datatables.net/reference/api/row().child()
     * 
     * Args:
     *   link (jQuery node): Node of the edit link.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    editRow: function(link) {
        var ds = this;
        // prevent multiple edits
        if(ds.mode == "edit")
            return false;
        // set edit mode on add mode (create mode is retained)
        if(ds.mode == "add")
            ds.mode = "edit";
        // get and redraw row
        var row = ds.target.table.row($(link).closest('tr'))
            .invalidate('data').draw(false);
        // open edit area
        row.child(ds.templates.edit(row.data())).show();
        $(row.child()).addClass('child');
        return false;
    },

    /**
     * Saves an edited row in target table.
     * 
     * Saves rows only in create/edit mode, ends in add mode.
     * 
     * Args:
     *   link (jQuery node): Node of the save link.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    saveRow: function(link) {
        var ds = this;
        // save only in create/edit mode
        if(ds.mode === "add")
            return false;
        // validate edit form
        var child = $(link).parents('tr');
        var editForm = child.find(".cs-datatables-edit");
        if(!ds.editFormValid(editForm))
            return false;
        // update data
        var row = ds.target.table.row(child.prev('tr'));
        var data = row.data();
        ds.updateData(data, editForm);
        // set add mode
        ds.mode = "add";
        // update and draw row
        row.data(data).draw();
        // close edit area
        row.child.remove();
        return false;
    },

    /**
     * Pins a modal.
     * 
     * Args:
     *   link (jQuery node): Node of the pin button.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    pinModal: function(link) {
        var ds = this;
        $(link).toggleClass('pinned');
        $(link).blur();
        return false;
    },

    constructor: DatatableSequence

};

// Add DatatableSequence to deform object for global access
deform.DatatableSequence = DatatableSequence;
