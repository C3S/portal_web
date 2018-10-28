// dependancies
if(typeof deform == "undefined")
    throw new Error("'deform' is not included yet.");
if(typeof tmpl == "undefined")
    throw new Error("'tmpl' is not included yet.");
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
    might be created and edited. Adding, creating and editing rows is done via
    bootstrap modals. The templates are parsed with tpml.

    Additional deform field necessary:

        class ModeField(colander.SchemaNode):
            oid = "mode"
            schema_type = colander.String
            widget = deform.widget.HiddenWidget()
            validator = colander.OneOf(['add', 'create', 'edit'])
    
    Initialization in template:

        <tal:block metal:extend-macro="sequence"
                   i18n:domain="<DOMAIN>">
            <script metal:fill-slot="settings">
                var datatableSequenceSettings = {
                    apiPath: "<PATH>",
                    apiArgs: function(args)
                    unique: "<COLUMNNAME>" | function(data)
                    tpl: "<BASETEMPLATEID>",
                    actions: ['add', 'create', 'edit']
                    columns: [<DATATABLECOLUMNS>],
                }
            </script>
        </tal:block>

    Additional column attributes for custom columns:

        datatableSequence: {
            targetPosition: "displayed" | "collapsed" | "invisible"
            sourcePosision: "displayed" | "collapsed" | "invisible"
            widgetType:     string (deform widget type)
            footerSearch:   true | false (creates footer search field)
            createValue:    string (default: "")
            createShow:     true | false (default: false, shows field in table]
        }

    Functional columns:
    
        target table
        - orderable: order number (if table is orderable)
        - more: zoom-in/out icon to show details, if available
        - controls: control links (edit, remove)
        - sequence: contains html code for colander sequence item
        - mode: add|create|edit
        - errors: error feedback from colander validation

        source table
        - more: zoom-in/out icon to show details, if available
        - controls: control links (add)

    TODO:
    - support all other deform widget types
*/

var DatatableSequence = function(vars) {

    // self reference
    var ds = this;

    // deform
    this.oid = vars.oid;
    this.name = vars.name;
    this.title = vars.title;
    this.minLen = vars.minLen ? parseInt(vars.minLen) : 0;
    this.maxLen = vars.maxLen ? parseInt(vars.maxLen) : 10000;
    this.errormsg = vars.errormsg ? vars.errormsg : false;
    this.orderable = vars.orderable ? parseInt(vars.orderable) == 1 : false;
    this.proto = vars.proto;
    this.api = vars.api;
    this.apiPath = vars.apiPath;
    this.apiArgs = vars.apiArgs ? vars.apiArgs : false;

    // selectors
    var base = "datatable_sequence_" + ds.oid;
    this.registry = "deform.datatableSequences." + ds.oid;
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
        modalEdit:    "#" + base + "_modal_edit",
    };

    // templates
    base = "datatable_sequence";
    this.tpl = {
        container:    "#cs-tmpl-container",
        sequence:     vars.tpl ? vars.tpl : base + "_tpl_sequence",
        controls:     base + "_tpl_controls",
        target: {
            table:    base + "_tpl_target",
            controls: base + "_tpl_target_controls",
            show:     base + "_tpl_target_show",
            more:     base + "_tpl_more",
            details:  base + "_tpl_details",
        },
        source: {
            table:    base + "_tpl_source",
            controls: base + "_tpl_source_controls",
            more:     base + "_tpl_more",
            details:  base + "_tpl_details",
        },
        modal:        base + "_tpl_modal",
        create:       base + "_tpl_create",
        edit:         base + "_tpl_edit",
    };

    // datatable
    this.language = $(ds.sel.html).data('language');
    this.actions = vars.actions ? // enabled actions
                   $.parseJSON(vars.actions) :
                   ['add', 'create', 'edit'];
    this.columns = vars.columns;  // custom datatable columns
    this.unique = vars.unique;    // definition of uniqueness of data

    // events
    this.bind = [
        'closeAdd',
        'openCreate',
        'closeEdit',
        'search',
        'more',
        'showHide',
        'redrawAdd',
        'redrawTab',
    ];

    // table meta objects
    this.target = {
        // datatable table
        table: false,
        // computed columns
        columns: false,
        // table html node selector
        tableId: ds.sel.targetTable,
        // initial data
        data: $(ds.sel.html).data('data'),
    };
    this.source = {
        // datatable table
        table: false,
        // computed columns
        columns: false,
        // table html node selector
        tableId: ds.sel.sourceTable,
    };

};


DatatableSequence.prototype = {

    /**************************************************************************
        INIT
    **************************************************************************/

    /**
      * Loads the sequence templates and calls init
      */
    init: function() {
        var ds = this;
        $(ds.tpl.container).load(
            "/static/portal/tmpl/sequence.tmpl",
            function() { ds._init(); }
        );
    },

    /**
     * Initializes the datatable sequence.
     *
     * - Initializes columns
     * - Generates html code
     * - Initializes the target table
     * - Initializes the source table
     * - Binds the events
     * - Adds the instance to the datatableSequence registry
     */
    _init: function() {
        var ds = this;
        $(document).ready(function() {

            // initialize columns
            ds.target.columns = ds.targetColumns();
            ds.source.columns = ds.sourceColumns();

            // generate html
            $(ds.sel.html).append(
                tmpl(ds.tpl.sequence, {
                    lableClass: ds.minLen ? "required" : "",
                    errormsg: ds.errormsg,
                    ds: {
                        registry: ds.registry,
                        actions:  ds.actions,
                        name:     ds.name,
                        title:    ds.title,
                        source:   ds.source,
                        target:   ds.target,
                        tpl:      ds.tpl,
                        sel:      ds.sel,
                        language: ds.language,
                        sequence: '',
                    }
                })
            );

            // prepare orderable table
            var order = [
                [ ds.getColumnIndex(ds.target, 'mode'), "asc" ],
                [ 1, "asc" ]  // first displayed row
            ];
            if(ds.orderable) {
                order = [
                    [ 0, "asc" ]  // order column
                ];
                $.each(ds.target.data, function(index, data) {
                    data.order = index + 1;
                });
            }

            // initialize target table
            ds.target.table = $(ds.sel.targetTable).DataTable({
                data: ds.target.data,
                language: ds.language,
                paging: false,
                info: false,
                searching: false,
                autoWidth: false,
                fixedHeader: false,
                rowReorder: ds.orderable ? {
                    dataSrc: 'order',
                    selector: 'td:nth-child(1)'
                } : false,
                responsive: {
                    details: {
                        renderer: function(api, rowIdx, columns) {
                            if(!ds.dataHidden(ds.target.table.row(rowIdx)))
                                return false;
                            return tmpl(ds.tpl.target.details, {
                                columns: columns
                            });
                        },
                        type: 'column'
                    }
                },
                columns: ds.target.columns,
                createdRow: function(row, data, dataIndex){
                    if(data.errors)
                        $(row).addClass('warning');
                },
                order: order
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
                    url: ds.api + "/" + ds.apiPath,
                    xhrFields: {withCredentials: true},
                    dataType: "json",
                    data: function(args) {
                        if(ds.apiArgs)
                            ds.apiArgs(args);
                        return JSON.stringify(args);
                    }
                },
                responsive: {
                    details: {
                        renderer: function(api, rowIdx, columns) {
                            if(!ds.dataHidden(ds.source.table.row(rowIdx)))
                                return false;
                            return tmpl(ds.tpl.source.details, {
                                columns: columns
                            });
                        },
                        type: 'column'
                    }
                },
                columns: ds.source.columns,
                order: [
                    [ 1, "asc" ]  // first displayed row
                ]
            });

            // bind events
            ds.events = ds.events();
            $.each(ds.bind, function(index, event) { ds.events[event](); });

            // redraw (to display zoom icon in more column)
            ds.target.table.rows().invalidate('data').draw(false);

            // add datatable sequence to registry (for global access)
            deform.datatableSequences[ds.oid] = ds;

        });
    },


    /**************************************************************************
        COLUMNS
    **************************************************************************/

    /**
     * Get merged custom and functional columns of target table.
     *
     * Returns:
     *   array: merged columns.
     */
    targetColumns: function() {
        var ds = this;
        // orderable
        if(ds.orderable)
            $.each(ds.columns, function(index, column) {
                column.orderable = false;
            });
        // clone custom columns
        var customCols = $.extend(true, {}, ds.getSortedColumns());
        // render first field
        // customCols.displayed[0].render = function(data, type, row, meta) {
        //     if(type !== 'display')
        //         return data;
        //     if(row.mode === "add")
        //         return tmpl.encode(data);
        //     // show data, if column is the only create field
        //     var count = 0;
        //     var show = [];
        //     $.each(ds.columns, function(index, column) {
        //         if(column.datatableSequence &&
        //            column.datatableSequence.createShow) {
        //             show.push(column);
        //             count++;
        //         }
        //     });
        //     if(count == 1 && show[0].data == customCols.displayed[0].data)
        //         return tmpl.encode(data);
        //     // show table with all created row data
        //     return tmpl(ds.tpl.target.show, {
        //         data: data,
        //         row: row,
        //         columns: show,
        //         language: ds.language,
        //     });
        // };
        // return merged columns
        var targetColumns = [
            {
                name: "order",
                data: "order",
                className: "text-center all more",
                width: "30px",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    if(type !== 'display')
                        return data;
                    return '<span class="glyphicon glyphicon-move"></span>';
                }
            },
            {
                name: "more",
                data: null,
                className: "text-center all more",
                width: "30px",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    return tmpl(ds.tpl.target.more, {
                        hidden:   ds.target.table ?
                                  ds.dataHidden(ds.target.table.row(meta.row)) :
                                  false,
                        data:     data,
                        language: ds.language,
                    });
                },
            },
            customCols.displayed,
            {
                name: "controls",
                data: null,
                className: "text-right nowrap all cs-datatables-col-controls",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    return tmpl(ds.tpl.target.controls, {
                        registry:  ds.registry,
                        actions:   ds.actions,
                        data:      data,
                        editClass: data.errors ? 'btn-danger' : 'btn-default',
                        language:  ds.language,
                    });
                },
            },
            customCols.collapsed,
            {
                name: "sequence",
                data: "sequence",
                className: "sequence hidden",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    if(data instanceof jQuery) {
                        var $row = $(ds.target.table.row(meta.row).node());
                        var sequence = $row.children(".sequence");
                        if(sequence)
                            sequence.empty();
                            sequence.append(data);
                        return "";
                    }
                    return data;
                },
            },
            customCols.invisible,
            {
                name: "mode",
                data: "mode",
                visible: false,
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    if(type === 'sort') {
                        switch(data) {
                            case 'create':
                                return 1;
                            case 'edit':
                                return 2;
                            case 'add':
                                return 3;
                        }
                    }
                    if(type === 'display')
                        return tmpl.encode(data);
                    return data;
                },
            },
            {
                name: "errors",
                data: "errors",
                visible: false,
                orderable: false,
                searchable: false,
            }
        ].flat();
        if(!ds.orderable)
            targetColumns.shift();
        return targetColumns;
    },

    /**
     * Get merged custom and functional columns of source table.
     *
     * Returns:
     *   array: merged columns.
     */
    sourceColumns: function() {
        var ds = this;
        // clone custom columns
        var customCols = $.extend(true, {}, ds.getSortedColumns());
        // return merged columns
        var sourceColumns = [
            {
                name: "more",
                data: null,
                className: "text-center all more",
                width: "30px",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    return tmpl(ds.tpl.source.more, {
                        hidden:   ds.source.table ?
                                  ds.dataHidden(ds.source.table.row(meta.row)) :
                                  false,
                        data:     data,
                        language: ds.language,
                    });
                },
            },
            customCols.displayed,
            {
                name: "controls",
                data: null,
                className: "text-right nowrap all cs-datatables-col-controls",
                orderable: false,
                searchable: false,
                render: function(data, type, row, meta) {
                    return tmpl(ds.tpl.source.controls, {
                        registry: ds.registry,
                        meta:     meta,
                        added:    ds.rowAdded(row),
                        language: ds.language,
                    });
                },
            },
            customCols.collapsed,
            customCols.invisible,
        ].flat();
        return sourceColumns;
    },


    /**************************************************************************
        ACTIONS
    **************************************************************************/

    /**
     * Adds a row from source to target table.
     * 
     * Args:
     *   rowId (int): Row ID of the row to add.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    addRow: function(rowId) {
        var ds = this;
        // prevent multiple edits
        if(ds.locked())
            return false;
        // get data
        var data = ds.source.table.row(rowId).data();
        // prevent multiple addition
        if(ds.rowAdded(data))
            return false;
        // set data
        data.mode = "add";
        data.errors = "";
        data.sequence = ds.newSequence(data).node;
        // set order number for orderable tables
        if(ds.orderable) {
            var orderNum = 0;
            $.each(ds.target.table.data(), function(index, data) {
                if(data.order > orderNum)
                    orderNum = data.order;
            });
            data.order = orderNum + 1;
        }
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
        if(typeof obj === "number")  // for indexes
            row = ds.target.table.row(obj);
        else {                       // for links
            tr = $(obj);
            if(!tr.is('tr'))
                tr = tr.parents('tr');
            row = ds.target.table.row(tr);
        }
        // remove row
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
     * Creates a row in target table.
     *
     * Args:
     *   link (jQuery node): Node of the create link.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    createRow: function(link) {
        var ds = this;
        // prevent multiple creations
        if(ds.locked())
            return false;
        // get form
        var form = $(link).closest('.modal-body').find('.deform-sequence-item');
        // validate edit form
        if(!ds.validateForm(form))
            return false;
        // get data template
        var data = ds.getDataTemplate();
        // set order number for orderable tables
        if(ds.orderable) {
            var orderNum = 0;
            $.each(ds.target.table.data(), function(index, data) {
                if(data.order > orderNum)
                    orderNum = data.order;
            });
            data.order = orderNum + 1;
        }
        // update data and redraw row
        ds.updateData(data, form);
        ds.target.table.row.add(data).draw();
        // close modal
        $(ds.sel.modalCreate).modal('hide');
        return false;
    },

    /**
     * Edits a row in target table.
     * 
     * Args:
     *   link (jQuery node): Node of the edit link.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    editRow: function(link) {
        var ds = this;
        // get elements
        var modal = $(ds.sel.modalEdit);
        var modalIndex = modal.find('.modal-body > input[name="index"]');
        var modalTitle = modal.find('.modal-title');
        var modalSequence = modal.find('.modal-body .deform-sequence-container');
        var row = ds.target.table.row($(link).closest('tr'));
        var data = row.data();
        console.log(data.sequence);
        // update modal
        modalIndex.val(row.index());
        modalTitle.text(ds.language.custom.edit);
        modalSequence.empty();
        modalSequence.append(data.sequence);
        // open modal
        modal.modal('show');
        return false;
    },

    /**
     * Saves an edited row in target table.
     * 
     * Args:
     *   link (jQuery node): Node of the save link.
     * 
     * Returns:
     *   false: Prevents link execution.
     */
    saveRow: function(link) {
        var ds = this;
        // prevent multiple saves
        if(ds.locked())
            return false;
        // get elements
        var modal = $(link).closest('.modal');
        var index = modal.find('.modal-body > input[name="index"]').val();
        var form = modal.find('.deform-sequence-item');
        // validate edit form
        if(!ds.validateForm(form))
            return false;
        // update data and draw row
        var row = ds.target.table.row(index);
        var data = row.data();
        ds.updateData(data, form);
        row.data(data).draw();
        // close modal
        modal.modal('hide');
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


    /**************************************************************************
        EVENTS
    **************************************************************************/

    events: function() {
        var ds = this;
        return {
        
            /**
             * Redraws target and source table after changing a navigation tab.
             * 
             * Binds to the bootstrap navigation tabs. Fixes the table width.
             */
            redrawTab: function() {
                $("a[data-toggle=\"tab\"]").on("shown.bs.tab", function (e) {
                    ds.source.table.columns.adjust();
                    ds.target.table.columns.adjust();
                });
            },

            /**
             * Redraws source table after opening add modal.
             * 
             * Binds to the bootstrap navigation tabs. Fixes the table width.
             */
            redrawAdd: function() {
                $(ds.sel.modalAdd).on('show.bs.modal', function (e) {
                    setTimeout(ds.source.table.columns.adjust, 200);
                });
            },

            /**
             * Shows/Hides target table if data is present/absent.
             *
             * Shows/Hides controls if maxLen is (not) reached.
             * 
             * Binds to the datatables init and pre draw event.
             */
            showHide: function() {
                ds.target.table.on('preDraw', function() {
                    var rows = ds.target.table.data().count();
                    // show/hide target table
                    if(rows > 0)
                        $(ds.sel.targetTable).show();
                    else
                        $(ds.sel.targetTable).hide();
                    // show/hide controls
                    if(rows < ds.maxLen)
                        $(ds.sel.controls).show();
                    else {
                        $(ds.sel.controls).hide();
                        $(ds.sel.modalAdd).modal('hide');
                    }
                });
            },

            /**
             * Opens and closes the details for target and source tables.
             * 
             * Binds to the more column on click event.
             */
            more: function() {
                $.each([ds.source, ds.target], function(index, obj) {
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
                });
            },

            /**
             * Initializes the column search of source table.
             * 
             * Binds to individual column search input fields.
             */
            search: function() {
                // bind keyup to search updates
                ds.source.table.columns().every(function () {
                    var that = this;
                    $('input', this.footer()).on('keyup change', function() {
                        if (that.search() !== this.value) {
                            that.search( this.value ).draw();
                        }
                    });
                });
            },

            /**
             * Resets search forms of source table, when add modal is closed.
             *
             * Does not reset, if the modal is pinned.
             */
            closeAdd: function() {
                $(ds.sel.modalAdd).on('hidden.bs.modal', function (e) {
                    // consider pin
                    if($(ds.sel.modalAdd + ' .pin').hasClass('pinned'))
                        return;
                    // reset individual search fields
                    ds.source.table.columns().every(function () {
                        var footer = $('input', this.footer()).val('').change();
                    });
                    // reset main search field
                    ds.source.table.search('');
                    //redraw
                    ds.source.table.draw();
                });
            },

            /**
             * Generates a new create form, when create modal is opened.
             */
            openCreate: function() {
                $(ds.sel.modalCreate).on('show.bs.modal', function(e) {
                    // new creation form
                    var container = $(ds.sel.modalCreate).find(
                        '.modal-body .deform-sequence-container');
                    var sequence = ds.newSequence();
                    // append sequence
                    var appendSequence = function() {
                        var deferred = $.Deferred();
                        container.empty();
                        container.append(sequence.node);
                        deferred.resolve();
                        return deferred.promise();
                    };
                    // process deform callbacks
                    appendSequence().done(function(){
                        $(deform.callbacks).each(function(num, item) {
                            var oid = item[0];
                            var callback = item[1];
                            var newid = sequence.idmap[oid];
                            if (newid)
                                callback(newid);
                        });
                        deform.clearCallbacks();
                        var ce = jQuery.Event("change");
                        $('#deform').trigger(ce);
                    });
                });
            },

            /**
             * Returns the creation form to the datatables row on cancel
             */
            closeEdit: function() {
                $(ds.sel.modalEdit).on('hidden.bs.modal', function(e) {
                    var modal = $(ds.sel.modalEdit);
                    var index = modal.find(
                        '.modal-body > input[name="index"]').val();
                    var sequence = modal.find(
                        '.modal-body .deform-sequence-item');
                    if(sequence.length) {
                        var row = ds.target.table.row(index);
                        var data = row.data();
                        ds.updateSequence(sequence, data);
                        row.data(data).draw();
                    }
                });
            },

        };

    },


    /************************************************************************** 
        AUXILIARY 
    **************************************************************************/

    /** 
     * Lock mechanism to prevent multiple actions
     */
    locked: function() {
        var ds = this;
        if(typeof ds.lock === "undefined")
            ds.lock = false;
        if(ds.lock)
            return true;
        ds.lock = true;
        setTimeout(function() { ds.lock = false; }, 200);
        return false;
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

        if(data)
            ds.updateSequence($htmlnode, data);

        return {
            node: $htmlnode,
            idmap: idmap
        };
    },

    /**
     * Checks, if a row already added.
     *
     * If ds.unique is a string, that string is the name of the column, which
     * defines the uniquness of a row.
     *
     * If ds.unique is a function, uniqeness is defined by the return value
     * of that function, given a data array of the row.
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
            // no uniqness, more identical rows are possible
            default:
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
        //sequence.find("input[name='mode']").val(data.mode);
        sequence.find("input[name='mode']").attr('value', data.mode);
        // update data columns
        var query = '';
        $.each(ds.columns, function(index, column) {
            switch(column.datatableSequence.widgetType) {

                case 'TextInputWidget':
                    query = "input[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
                    sequence.find(query).attr('value', data[column.data]);
                    break;

                case 'TextAreaWidget':
                    query = "textarea[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
                    break;

                case 'Select2Widget':
                    query = "select[name='" + column.name + "']";
                    var option = sequence.find(query + " option").filter(
                        function () {
                            return $(this).html() == data[column.data];
                        }).val();
                    if(option)
                        sequence.find(query).val(option).trigger('change');
                    break;

                case 'HiddenWidget':
                    query = "input[name='" + column.name + "']";
                    sequence.find(query).val(data[column.data]);
            }
        });
        // save updated html code back into the row data again
        data.sequence = sequence;
    },

    /**
     * Updates row data and sequence item html code with form data.
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
            switch(column.datatableSequence.widgetType) {

                case 'TextInputWidget':
                    element = form.find("input[name='" + column.name + "']");
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
                    break;

                case 'TextAreaWidget':
                    element = form.find("textarea[name='" + column.name + "']");
                    if(element.length === 0)
                        return;
                    value = element.val();
                    data[column.data] = value;
                    break;

                case 'Select2Widget':
                    element = form.find("select[name='" + column.name + "']");
                    if(element.length === 0)
                        return;
                    value = element.find("option:selected").text();
                    data[column.data] = value;
                    break;

                case 'HiddenWidget':
                    break;  // don't update hidden fields
            }
        });
        // update sequence
        ds.updateSequence(form, data);
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
        data.sequence = ds.newSequence(data).node;
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
    validateForm: function(form) {
        var ds = this;
        var valid = true;
        // for all columns
        $.each(ds.columns, function(index, column) {
            // get form group
            group = $(form).find('.item-' + column.name);
            if(!group)
                return;
            // get required
            var required = group.find('.required');
            // get field
            var field, value = false;
            switch(column.datatableSequence.widgetType) {

                case 'TextAreaWidget':
                    field = form.find("textarea[name='" + column.name + "']");
                    value = field.val();
                    break;

                case 'TextInputWidget':
                    field = form.find("input[name='" + column.name + "']");
                    value = field.val();
                    break;

                case 'Select2Widget':
                    field = form.find("select[name='" + column.name + "']");
                    value = field.find("option:selected").text();
                    break;
                
                case 'HiddenWidget':
                    return;  // don't get hidden fields
            }
            // prevent emtpy required fields
            if(required && !value) {
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

    constructor: DatatableSequence

};

// Add DatatableSequence to deform object for global access
deform.DatatableSequence = DatatableSequence;