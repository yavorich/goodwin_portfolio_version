from django.utils.encoding import force_str
from django.db.models import Case, When, Value, CharField


class WithChoices(Case):
    def __init__(self, model, field, condition=None, then=None, **lookups):
        fields = field.split("__")
        for f in fields:
            model = model._meta.get_field(f)

            if model.related_model:
                model = model.related_model

        choices = dict(model.flatchoices)
        whens = [
            When(**{field: k, "then": Value(force_str(v))}) for k, v in choices.items()
        ]
        return super().__init__(*whens, output_field=CharField())
