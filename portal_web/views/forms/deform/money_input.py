# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import json
from decimal import Decimal, ROUND_HALF_UP

import colander
from deform.widget import MoneyInputWidget as DeformMoneyInputWidget
from deform.compat import string_types


class MoneyInputWidget(DeformMoneyInputWidget):
    def __init__(self, *args, **kwargs):
        # default options (different from deform widget docs!)
        # see https://www.npmjs.com/package/jquery-maskmoney
        options = {
            'prefix': '',
            'suffix': ' €',
            'affixesStay': False,
            'thousands': '.',
            'decimal': ',',
            'precision': 2,
            'allowZero': True,
            'allowNegative': False,
        }
        # TODO: get user language, set values according to Currency model
        if 'options' in kwargs:
            options.update(kwargs['options'])
        kwargs['options'] = options
        super().__init__(*args, **kwargs)

    def serialize(self, field, cstruct, **kw):
        if cstruct in (colander.null, None):
            cstruct = ""
        readonly = kw.get("readonly", self.readonly)
        options = kw.get("options", self.options)
        if options is None:
            options = {}

        thousands = ","
        decimal = "."
        prefix = ""
        suffix = ""
        if options:
            thousands = options.get("thousands", ",")
            decimal = options.get("decimal", ".")
            prefix = options.get("prefix", "")
            suffix = options.get("suffix", "")
        if cstruct:
            cstruct = f"{Decimal(cstruct):,}"
            cstruct = cstruct.replace(",", "T")
            cstruct = cstruct.replace(".", "D")
            cstruct = cstruct.replace("T", thousands)
            cstruct = cstruct.replace("D", decimal)
            if options.get("affixesStay", False):
                cstruct = f"{prefix}{cstruct}{suffix}"

        options = json.dumps(dict(options))
        kw["mask_options"] = options
        values = self.get_template_values(field, cstruct, kw)
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        elif not isinstance(pstruct, string_types):
            raise colander.Invalid(field.schema, "Pstruct is not a string")
        pstruct = pstruct.strip()

        thousands = ","
        decimal = "."
        prefix = ""
        suffix = ""
        options = dict(getattr(self, 'options', {}))
        if options:
            thousands = options.get("thousands", ",")
            decimal = options.get("decimal", ".")
            prefix = options.get("prefix", "")
            suffix = options.get("suffix", "")
        pstruct = pstruct.replace(thousands, "")
        if decimal != ".":
            pstruct = pstruct.replace(decimal, ".")
        if prefix:
            pstruct = pstruct.replace(prefix, "")
        if suffix:
            pstruct = pstruct.replace(suffix, "")

        if not pstruct:
            return colander.null
        return pstruct


class MoneyInputField(colander.SchemaNode):
    schema_type = colander.Money
    widget = MoneyInputWidget()
