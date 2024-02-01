from django import forms
from localized_fields import widgets


class LocalizedCharFieldWidget(widgets.LocalizedCharFieldWidget):
    template_name = "multiwidget.html"


class LocalizedTextFieldWidget(widgets.LocalizedCharFieldWidget):
    template_name = "multiwidget.html"
    widget = forms.Textarea


class LocalizedFileWidget(widgets.LocalizedFileWidget):
    template_name = "multiwidget.html"


class LocalizedURLWidget(widgets.LocalizedCharFieldWidget):
    template_name = "multiwidget.html"
    widget = forms.URLInput
