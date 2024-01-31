from localized_fields.forms import LocalizedFieldForm
from localized_fields.value import LocalizedStringValue

from .widgets import LocalizedCharFieldWidget


class LocalizedCharFieldForm(LocalizedFieldForm):
    widget = LocalizedCharFieldWidget
    value_class = LocalizedStringValue
