from import_export.fields import Field


class ReadOnlyField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly = True
