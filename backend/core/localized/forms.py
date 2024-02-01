from django.core.exceptions import ValidationError
from localized_fields import forms
from localized_fields.value import LocalizedStringValue
from django.forms import fields

from .widgets import (
    LocalizedCharFieldWidget,
    LocalizedFileWidget,
    LocalizedURLWidget,
    LocalizedTextFieldWidget,
)


class LocalizedCharFieldForm(forms.LocalizedFieldForm):
    widget = LocalizedCharFieldWidget
    value_class = LocalizedStringValue


class LocalizedTextFieldForm(forms.LocalizedFieldForm):
    widget = LocalizedTextFieldWidget
    value_class = LocalizedStringValue


class LocalizedFileFieldForm(forms.LocalizedFileFieldForm):
    widget = LocalizedFileWidget


class LocalizedURLFieldForm(forms.LocalizedFieldForm):
    widget = LocalizedURLWidget
    value_class = LocalizedStringValue
    field_class = fields.URLField

    def clean(self, value, initial=None):
        """Most part of this method is a copy of
        django.forms.MultiValueField.clean, with the exception of initial value
        handling (this need for correct processing FileField's).

        All original comments saved.
        """
        if initial is None:
            initial = [None for x in range(0, len(value))]
        else:
            if not isinstance(initial, list):
                initial = self.widget.decompress(initial)

        clean_data = []
        errors = []
        if not value or isinstance(value, (list, tuple)):
            is_empty = [v for v in value if v not in self.empty_values]
            if (not value or not is_empty) and (not initial or not is_empty):
                if self.required:
                    raise ValidationError(
                        self.error_messages["required"], code="required"
                    )
        else:
            raise ValidationError(self.error_messages["invalid"], code="invalid")

        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None

            try:
                field_initial = initial[i]
            except IndexError:
                field_initial = None

            if field_value in self.empty_values and field_initial in self.empty_values:
                if self.require_all_fields:
                    # Raise a 'required' error if the MultiValueField is
                    # required and any field is empty.
                    if self.required:
                        raise ValidationError(
                            self.error_messages["required"], code="required"
                        )
                elif field.required:
                    # Otherwise, add an 'incomplete' error to the list of
                    # collected errors and skip field cleaning, if a required
                    # field is empty.
                    if field.error_messages["incomplete"] not in errors:
                        errors.append(field.error_messages["incomplete"])
                    continue
            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter. Skip duplicates.
                errors.extend(m for m in e.error_list if m not in errors)
        if errors:
            raise ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out
