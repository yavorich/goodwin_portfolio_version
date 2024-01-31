from localized_fields.fields import LocalizedField
from localized_fields.value import LocalizedStringValue

from .forms import LocalizedCharFieldForm


class LocalizedCharField(LocalizedField):
    attr_class = LocalizedStringValue

    def formfield(self, **kwargs):
        defaults = {"form_class": LocalizedCharFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)
