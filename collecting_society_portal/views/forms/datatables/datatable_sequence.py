import logging
import deform
import colander
import json

from pyramid.renderers import get_renderer

from ....services import _

log = logging.getLogger(__name__)


class DatatableSequence(colander.SequenceSchema):
    def __init__(self, *arg, **kw):
        if 'min_len' in kw and kw['min_len'] > 0:
            min_err = _(u'Please add at least one entry.')
            if kw['min_len'] > 1:
                min_err = _(
                    u'Please add at least a total of {} entries.'
                ).format(kw['min_len'])
            self.validator = colander.Length(
                min=kw['min_len'],
                min_err=_(min_err)
            )
        super(DatatableSequence, self).__init__(*arg, **kw)


class DatatableSequenceWidget(deform.widget.SequenceWidget):

    category = 'structural'
    item_template = 'datatables/sequence_item'

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

    def language(self):
        _ = self.request.localizer.translate
        d = getattr(self, 'domain', 'collecting_society_portal')
        return json.dumps({
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
        })

    def get_template_values(self, field, cstruct, kw):
        settings = self.request.registry.settings
        api = getattr(self, 'api', ''.join([
            settings['api.datatables.url'], '/',
            settings['api.datatables.version']
        ]))
        kw.update({
            'request': self.request,
            'dumps': json.dumps,
            'api': api,
            'data': self.rows(field, cstruct, kw),
            'language': self.language(),
            'sequence': get_renderer(
                "collecting_society_portal:"
                "templates/deform/datatables/sequence.pt"
            ).implementation(),
            '_': _
        })
        return super(DatatableSequenceWidget, self).get_template_values(
            field, cstruct, kw)
