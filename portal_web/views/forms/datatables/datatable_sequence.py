import logging
import deform
import colander
import json

from pyramid.renderers import get_renderer

from ....services import _, benchmark

log = logging.getLogger(__name__)


@colander.deferred
def defered_datatable_sequence_validator(node, kw):
    missing = getattr(node, 'missing')
    min_len = getattr(node, 'min_len', False)
    if missing == colander.required:
        if min_len and min_len > 0:
            min_err = _('Please add at least one entry.')
            if min_len > 1:
                min_err = _(
                    'Please add at least a total of {} entries.'
                ).format(kw['min_len'])
            return colander.Length(
                min=min_len,
                min_err=_(min_err)
            )


class DatatableSequence(colander.SequenceSchema):
    """
    Overview
    --------

    The most distinct UI element of our web framework is the DatatableSequence.
    On our webpages we needed a solution for
    1. records to choose from tables of existing objects (add/remove),
    2. create new records, mostly for Many2One object relations (create/edit/
       remove)

    Technical Basis
    ---------------

    - Chameleon [1]: Template Engine
    - Deform [2]: Form-Generation-Library
    - Colander [3]: Backend for validation & De/serialization of data
    - DataTables: A JavaScript module for interactive html tables

    Note: The connections of the first three are shown in detail in the
    Redmine Wiki [4].

    Example
    -------

    Suppose you have a record 'person' with fields 'id', 'name' and 'gender',
    first you would want to feed the structure to Datatable in you page+
    template:

        >>> <script>
        >>>     var datatableSequenceSettings = {
        >>>         apiPath: "person",
        >>>         unique: "id",
        >>>         columns: [
        >>>             {
        >>>                 name: "name",
        >>>                 title: "${_('Name')}",
        >>>                 data: "name",
        >>>                 className: "all",
        >>>                 orderable: true,
        >>>                 searchable: true,
        >>>                 render: $.fn.dataTable.render.text(),
        >>>                 datatableSequence: {
        >>>                     position: "displayed",
        >>>                     widgetType: 'TextInputWidget',
        >>>                     footerSearch: true,
        >>>                     createShow: true,
        >>>                 }
        >>>             },
        >>>             {
        >>>                 name: "gender",
        >>>                 title: "${_('Gender')}",
        >>>                 data: "gender",
        >>>                 className: "all",
        >>>                 orderable: true,
        >>>                 searchable: false,
        >>>                 render: $.fn.dataTable.render.text(),
        >>>                 datatableSequence: {
        >>>                     position: "displayed",
        >>>                     widgetType: 'Select2Widget',
        >>>                     footerSearch: true,
        >>>                     createShow: true,
        >>>                 }
        >>>             },
        >>>                 name: "id",
        >>>                 title: "${_('ID')}",
        >>>                 data: "id",
        >>>                 className: "all",
        >>>                 orderable: true,
        >>>                 searchable: true,
        >>>                 render: $.fn.dataTable.render.text(),
        >>>                 datatableSequence: {
        >>>                     position: "displayed",
        >>>                     widgetType: 'TextInputWidget',
        >>>                     footerSearch: true,
        >>>                     createShow: true,
        >>>                 }
        >>>             },
        >>>     };
        >>> </script>

    Then a `DatatableSequence` can be defined:

        >>> def prepare_required(value):
        >>>     # oid required for add/edit
        >>>     if value['mode'] != "create" and value['oid'] == "IGNORED":
        >>>         value['oid'] = ""
        >>>     return value
        >>>
        >>> @colander.deferred
        >>> def deferred_location_space_category_widget(node, kw):
        >>>     values = [('m', 'male'), ('f', 'female'), ('o', 'other')]
        >>>     # deferred means that these values don't obey the declarative
        >>>     # context and could be read from a database while the
        >>>     # application is running
        >>>     return deform.widget.Select2Widget(values=values)
        >>>
        >>> class NameField(colander.SchemaNode):
        >>>     oid = "name"
        >>>     schema_type = colander.String
        >>>     widget = deform.widget.TextInputWidget()
        >>>
        >>> class GenderField(colander.SchemaNode):
        >>>     oid = "gender"
        >>>     schema_type = colander.String
        >>>     widget = deferred_gender_widget
        >>>
        >>> class IdField(colander.SchemaNode):
        >>>     oid = "id"
        >>>     schema_type = colander.String
        >>>
        >>> class PersonSchema(colander.Schema):
        >>>     name = NameField()
        >>>     gender = GenderField()
        >>>     id = IdField()
        >>>     preparer = [prepare_required]
        >>>     # the preparer sets dummy values in the oid fields in newly
        >>>     # created records
        >>>
        >>> class PersonSequence(DatatableSequence):
        >>>     person_sequence = PersonSchema()
        >>>     widget = person_sequence_widget
        >>>     actions = ['create', 'edit']

    Finally, the `DatatableSequence` can be used in your web page:

        >>> class CreatePersonSchema(colander.Schema):
        >>>     title = _(u"Create a Person")
        >>>     spaces = LocationSpaceSequence(
        >>>         title=_("Persons"),
        >>>         min_len=1,  # at least one person needed
        >>>         language_overrides={
        >>>             "custom": {"create": _(u"Create It")}
        >>>         })  # allows to inject translations

    Note: When an 'add' action is used, you need to implement a special api
          for Datatables.

    Requirements
    -------------

    - Interface for own/foreign objects to the
        - Display (list)
        - Create (create)
        - Edit (edit)
        - Add (add)
    It was crucial that *own* objects were newly creatable
    as well as existing *foreign* objects could be added,
    preferably in a form.
    - For ads (list):
        - client-side sorting
        - client-side filtering
    - For adding (add): Recourse to large data sets with
        - Server-side paging
        - Server-side filtering
    - Since complex objects are created, no reload is desired
    and a gradual user guidance becomes necessary
    - The element is needed several times per object
    (e.g. release: publisher, labels, tracks, etc.)
    - Some records require the two-tier embedding of the UI element
    (e.g. Creation -> Contribution [1st table] -> Artist [2nd table])
    - Internationalization
    - Client side validation if possible


    Solution
    ------

    - Methods
        - Docking to "Colander/Deform" [5]: Derive objects from Sequence
            - `DatatableSequence(colander.SequenceSchema)` [6, 7]
            - `DatatableSequenceWidget(deform.widget.SequenceWidget):` [8,9]
        - Embedding of "Datatables" [10] for
            - Tables as GUI-Elements (list) [11] [11
            - Ajax Handling (add) [12]
        - Use of "Bootstrap Modals" [13] for step-by-step user guidance
        - Benefits of "tpml 14] for client-side templates [15, 16] for
            - Datatables (e.g. sequence, controls, source/target table, ...)
            - Modals

    - Server side
        - Colander scheme [6]
            - Only validation adapted
        - Deform Widget [7]:
        - Sequence template created [17], linked to widget [18]
            This is delivered by the JS, which is used to configure everything
            [19] and is initialized [20].
            - Item-Template (Formlar-Template create/edit) is created [21],
            linked with widget [22]. Basically a normal, recursive
            Render the form fields.
            - The function `prototype()` [23] also generates in a
            normal sequence [24] the form template, which is sent to the
            client. must be passed on, because new items *client side* are
            added can be added.
            - De-/Serialization [25, 26] not changed
            - The function `rows()` [27, 28] returns the initial record
            - Internationalization via forwarding the translations as
            variables to the template engine [29, 30] as JSON, so that the
            JS-Code that can read and fill the tmpl templates.
        - API for Ajax data retrieval via datatables [31]:
            - Created the schema required by Datatable, which is available for
            all Datatable APIs can be used [32, 33].

    - On the client side
        - Datatables
            - Tables: 2 Datatable Tables
                - Target: this.target.table (-> list) [11]
                    - The Target Table is the prefilled table
                    with the current records that are being saved.
                    - It contains the serialized data set that is stored by
                    the Deform widget again and
                    is deserialized. This is contained in an HTML form,
                    the corresponding HTML form elements are created via JS
                    generated and in a separate hidden column
                    is saved.
                - Source: this.source.table (-> add) [12].
                    - From the source table are saved when adding a
                    the data into the Target Table in the existing entry
                    is taken over.
                    - The Source Table contains the entire Ajax
                    Handling in combination with the corresponding
                    server-side API, makes JSON requests to it,
                    takes the JSON records from it and generates the
                    Selection table.
            - Columns:
                - For each individual sequence the desired
                columns according to the Datatable Options [34, see
                "Datatable - Columns"] [e.g. 35], because a
                automation in most cases does not meet the
                desired results ("Which columns are
                currently relevant in the view"?)
                - Functionally necessary columns are added via JS:

                    - target [36]:
                        - order: Sorting
                        - more: Show/hide columns (Responsiveness)
                        - controls: Buttons (Edit, Create, Delete)
                        - sequence: Hidden HTML form fields
                        - oid: oid of the sequence
                        - mode: create, edit, add (as a hint for server)
                        - errors: error list
                    - Source [37]:
                        - more: Show/hide columns (Responsiveness)
                        - controls: Buttons (Edit, Create, Delete)
                        - oid: oid of the sequence
        - Modals
            - There are 3 modals for the actions add, create and edit
            - While the Target Table is rendered directly on the page
            [38, 39], are
                - the source table is rendered in add modal [40, 41]
                - the form templates each
                    - in create Modal [42, 43], or
                    - rendered in edit Modal [44, 45].
            - The modals are rendered depending on the action (create, edit,
              add)
            is called and closed:
                - create: The form generated by Deform on the server side is
                called Template ("Prototype") is instantiated, with new IDs
                [46], displayed in the modal and saved in the
                sequence column.
                - edit: The either by Deform server generated and
                filled out, or by create created form is
                read from the sequence column, displayed in the modal and
                written back again when saving.
                - add: The modal with the source table is opened, at
                Adding an entry will create a new one from Deform on the server
                generated form template ("Prototype") is instantiated,
                with new IDs and with the data of the entry
                filled out.
        - interaction (deform.datatables.widget.js)
            - Acceptance of the Deform Template Variables [47].
            - Initialization [48]:
                - Generation of the HTML codes from the tmpl templates
                - Configuration of the columns
                - Initialization of the tables
                - Binding of the events
            - Mode configuration ("actions=['add', 'create', 'edit']")
                - The controls for the modes available on the client side
                add/create/edit' can be switched on/off [49]. From these
                The corresponding controls are dependent on switches,
                Tables and Modals created during initialization or
                omitted [e.g. 50, 51]. list' is mandatory, because it
                without a Target Table no data transfer or GUI
                would exist.
            - Action Functions [52]
                - This part takes the role of the controller
                - In the Actions the possible operations on the
                Target Table defined, which the user can trigger:
                    - addRow
                    - removeRow
                    - createRow
                    - editRow
                    - saveRow
                - This contains the corresponding logic for the
                state changes of the GUI element and the
                User guidance for the modals.
            - Events [53]:
                - Here different functions are defined, which are passed on to
                Datatables Events [54] can be bound, for example
                    - more: Button for hidden columns (Responsive)
                    - search: Initialization of the search at Source Table
                    - redrawAdd: Open Redraw Source Table at Modal
                    - etc.
            - Client side validation [55]:
                - By default, client-side fields are set to required
                checked.
            - Recursion
                - For the multi-level GUI, server and
                client-side code adapted to support DatatableSequences
                to be able to nest.


    Summary
    ---------------

    Thus, the standard functionality of Deform/Colander automatically generates
    a Framework for the delivery of datatables/bootstrap based
    sequences. DatatableSequences must be defined for each
    desired object once, then the DatatableSequence can be
    easily used. This includes:

    1. creating the colander scheme [e.g. 56], from which the form
    template is generated and at least fields for the functional
    Datatable must contain columns (mode, oid (?))

    Note: The latter could also be defined centrally and used to
            as well as the workaround with the prepare
            Functions [57])

    2. create the template [e.g. 58], which contains the JS configuration
    and must contain at least the following functions:
        - apiPath: End piece of the path to the API
    Optional:
        - columns: At least one column for the display is useful
        - actions: ['add', 'create', 'edit']: Switches for the modes that
        should be available on the client side (from the user's point of view
        in the sense from 'add/create/edit entry')
        - unique: Column whose content guarantees the uniqueness of an entry
        identified and, if defined, the multiple addition of
        prevented.
        - apiArgs: Communication from JSON Key/Values to the server at
        Request to the API in add Modal. Can be used for filtering
        [e.g. 59, 60, 61] or any other purpose of the Client->Server
        Communication
        - tpl: For a different tmpl base template prefix.
        Unlikely that this is needed, but with it
        other tmpl templates can be used.

    3. create the API service [e.g. 62] (if 'add' in actions is possible
    should be).

    4. inclusion of the DatatableSequence [e.g. 63].


    Miscellaneous
    -------------

    - Overwrite the Item-Template, if for each entry
    wants to execute certain JS code [e.g. 64].
    - Adjusting the displayed text of a column using the render function
    e.g. 65] (-> Standard Datatables); You can decide about type,
    which views of the data should be changed [66].
    - Client-side debugging/view of globally accessible JS object
    `deform.datatableSequences`


    References
    ----------

    [1]
    https://docs.pylonsproject.org/projects/pyramid-chameleon/en/latest/

    [2]
    https://docs.pylonsproject.org/projects/deform/en/latest/

    [3]
    https://docs.pylonsproject.org/projects/colander/en/latest/

    [4]
    https://redmine.c3s.cc/projects/collecting_society/wiki/Pyramid_Concepts#Forms

    [5]
    https://docs.pylonsproject.org/projects/deform/en/latest/widget.html#writing-your-own-widget

    [6]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L30

    [7]
    https://github.com/Pylons/deform/blob/master/deform/widget.py#L1491

    [8]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L45

    [9]
    https://github.com/Pylons/colander/blob/master/src/colander/__init__.py#L1095

    [10]
    https://datatables.net/

    [11]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L309

    [12]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L344

    [13]
    https://getbootstrap.com/docs/3.3/javascript/#modals

    [14]
    https://github.com/blueimp/JavaScript-Templates

    [15]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L255

    [16]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/backend.pt#L40

    [17]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/deform/datatables/sequence.pt

    [18]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L183

    [19]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/deform/datatables/sequence.pt#L36

    [20]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/deform/datatables/sequence.pt#L53

    [21]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/deform/datatables/sequence_item.pt

    [22]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L47

    [23]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L53

    [24]:
    https://github.com/Pylons/deform/blob/master/deform/widget.py#L1559

    [25]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L64

    [26]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L71

    [27]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L78

    [28]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L174

    [29]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L182

    [30]
    https://github.com/C3S/portal_web/blob/develop/portal_web/views/forms/datatables/datatable_sequence.py#L124

    [31]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/api/datatables/base.py

    [32]
    https://datatables.net/manual/server-side

    [33]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/api/datatables/base.py#L68

    [34]
    https://datatables.net/reference/option/

    [35]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/templates/deform/datatables/artist_sequence.pt#L11

    [36]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L413

    [37]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L536

    [38]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L257

    [39]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/backend.pt#L58

    [40]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L270

    [41]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/backend.pt#L100

    [42]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L280

    [43]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/backend.pt#L165

    [44]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L289

    [45]
    https://github.com/C3S/portal_web/blob/develop/portal_web/templates/backend.pt#L180

    [46]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L1185

    [47]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L99

    [48]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L227

    [49]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L159

    [50]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L265

    [51]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L345

    [52]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L593

    [53]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L819

    [54]
    https://datatables.net/reference/event/

    [55]
    https://github.com/C3S/portal_web/blob/develop/portal_web/static/js/deform.datatables.widget.js#L1453

    [56]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/forms/datatables/artist_sequence.py#L139

    [57]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/forms/datatables/artist_sequence.py#L19

    [58]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/templates/deform/datatables/artist_sequence.pt

    [59]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/templates/deform/datatables/artist_sequence.pt#L8

    [60]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/api/datatables/artist.py#L28

    [61]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/api/datatables/artist.py#L72

    [62]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/api/datatables/artist.py

    [63]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/views/forms/add_artist.py#L197

    [64]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/templates/deform/datatables/track_sequence_item.pt

    [65]
    https://github.com/C3S/collecting_society_web/blob/develop/collecting_society_web/templates/deform/datatables/original_sequence.pt#L28

    [66]
    https://datatables.net/manual/data/orthogonal-data

    """
    def __init__(self, *arg, **kw):
        min_len = kw.get('min_len')
        if min_len:
            self.min_len = min_len
        max_len = kw.get('max_len')
        if max_len:
            self.max_len = max_len
        missing = kw.get('missing')
        if missing:
            self.missing = missing
        super(DatatableSequence, self).__init__(*arg, **kw)
    validator = defered_datatable_sequence_validator


class DatatableSequenceWidget(deform.widget.SequenceWidget):
    category = 'structural'
    item_template = 'datatables/sequence_item'
    language_overrides = {}
    prototypes = {}
    source_data = []
    source_data_total = False

    def prototype(self, *args, **kwargs):
        with benchmark(self.request, name='datatables.prototype',
                       uid=self.template, scale=1000):
            return super(
                DatatableSequenceWidget, self).prototype(*args, **kwargs)
            # TODO: fix caching:
            # if self.item_template not in self.prototypes:
            #     self.prototypes[self.item_template] = super(
            #         DatatableSequenceWidget, self).prototype(*args, **kwargs)
            # return self.prototypes[self.item_template]

    def serialize(self, *args, **kwargs):
        """Serialize"""
        with benchmark(self.request, name='datatables.serialize',
                       uid=self.template, scale=1000):
            return super(
                DatatableSequenceWidget, self).serialize(*args, **kwargs)

    def deserialize(self, *args, **kwargs):
        """Deserialize"""
        with benchmark(self.request, name='datatables.deserialize',
                       uid=self.template, scale=1000):
            return super(
                DatatableSequenceWidget, self).deserialize(*args, **kwargs)

    def rows(self, field, cstruct, kw):
        if not cstruct:
            return
        # prepare data
        data = []
        for subfield in [x[1] for x in kw['subfields']]:
            row = subfield.cstruct
            for column in row:
                # substitue colander null values
                if row[column] == colander.null:
                    row[column] = ""
            for item in subfield:
                # use select text instead of value
                if isinstance(item.widget, deform.widget.SelectWidget):
                    for option in item.widget.values:
                        if option[0] == row[item.name]:
                            row[item.name] = item.translate(option[1])
            # provide rendered sequence
            row['sequence'] = subfield.render_template(
                self.item_template, parent=field)
            # provide errors
            row['errors'] = ""
            for child in subfield.children:
                if not child.error:
                    continue
                row['errors'] += (
                    '<small class="text-danger" tal:condition="error_name">'
                    + field.translate(child.errormsg) +
                    '</small>'
                )
            data.append(row)
        return json.dumps(data)

    def dictmerge(self, source, destination):
        """
        merges source dict int destinatio dict
        """
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                self.dictmerge(value, node)
            else:
                destination[key] = value
        return destination

    def language(self):
        _ = self.request.localizer.translate
        d = getattr(self, 'domain', 'portal_web')
        langdict = {
            # en (https://datatables.net/plug-ins/i18n/English)
            "sEmptyTable": _("No data available in table", d),
            "sInfo": _("Showing _START_ to _END_ of _TOTAL_ entries", d),
            "sInfoEmpty": _("Showing 0 to 0 of 0 entries", d),
            "sInfoFiltered": _("(filtered from _MAX_ total entries)", d),
            "sInfoThousands": _(",", d),
            "sLengthMenu": _("Show _MENU_ entries", d),
            "sLoadingRecords": _("Loading...", d),
            "sProcessing": _("Processing...", d),
            "sSearch": _("Search:", d),
            "sZeroRecords": _("No matching records found", d),
            "oPaginate": {
                "sFirst": _("First", d),
                "sLast": _("Last", d),
                "sNext": _("Next", d),
                "sPrevious": _("Previous", d)
            },
            "oAria": {
                "sSortAscending":  _(": activate to sort column ascending", d),
                "sSortDescending": _(": activate to sort column descending", d)
            },
            # custom
            "custom": {
                "search": _("Search", d),
                "new": _("New", d),
                "edit": _("Edit", d),
                "apply": _("Apply", d),
                "remove": _("Remove", d),
                "add": _("Add", d),
                "create": _("Create", d),
                "cancel": _("Cancel", d),
            }
        }
        if hasattr(self, "language_overrides"):
            return json.dumps(self.dictmerge(
                self.language_overrides, langdict))
        return json.dumps(langdict)

    def get_template_values(self, field, cstruct, kw):
        settings = self.request.registry.settings
        api = getattr(self, 'api', ''.join([
            settings['api.datatables.url'], '/',
            settings['api.datatables.version']
        ]))
        with benchmark(self.request, name='datatables.load',
                       uid=self.template, scale=1000):
            target_data = self.rows(field, cstruct, kw)
        kw.update({
            'request': self.request,
            'dumps': json.dumps,
            'api': api,
            'target': target_data,
            'source': json.dumps(self.source_data),
            'source_total': self.source_data_total,
            'language': self.language(),
            'sequence': get_renderer(
                "portal_web:"
                "templates/deform/datatables/sequence.pt"
            ).implementation(),
            '_': _
        })
        return super(DatatableSequenceWidget, self).get_template_values(
            field, cstruct, kw)
