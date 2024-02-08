from django.db.models import URLField
from localized_fields import fields
from localized_fields.value import LocalizedStringValue

from .forms import (
    LocalizedCharFieldForm,
    LocalizedTextFieldForm,
    LocalizedFileFieldForm,
    LocalizedURLFieldForm,
)


class LocalizedCharField(fields.LocalizedField):
    attr_class = LocalizedStringValue

    def formfield(self, **kwargs):
        defaults = {"form_class": LocalizedCharFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class LocalizedTextField(LocalizedCharField):
    def formfield(self, **kwargs):
        defaults = {"form_class": LocalizedTextFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class LocalizedURLField(LocalizedCharField):
    default_validators = URLField.default_validators
    description = URLField.description

    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs.setdefault("max_length", 200)
        super().__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 200:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {"form_class": LocalizedURLFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class LocalizedFileField(fields.LocalizedFileField):
    def formfield(self, **kwargs):
        defaults = {"form_class": LocalizedFileFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)
