from django.http import HttpResponse
from import_export.admin import ExportMixin


class NoConfirmMixin(ExportMixin):
    def export_no_confirm(self, request, queryset):
        formats = self.get_export_formats()
        file_format = formats[0]()

        export_data = self.get_export_data(
            file_format, request, queryset, encoding=self.to_encoding
        )
        content_type = file_format.get_content_type()
        response = HttpResponse(export_data, content_type=content_type)
        response["Content-Disposition"] = 'attachment; filename="%s"' % (
            self.get_export_filename(request, queryset, file_format),
        )
        return response


class NoConfirmExportMixin(NoConfirmMixin):
    def export_action(self, request):
        return self.export_no_confirm(request, self.get_export_queryset(request))


class ExportInlineMixin(NoConfirmMixin):
    template = "export_tabular.html"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.inline_class_name = self.__class__.__name__
        return formset


class ExportInlineModelAdminMixin:
    def response_change(self, request, obj):
        for inline_class in self.get_inline_instances(request, obj):
            if f"_export-{inline_class.__class__.__name__}" in request.POST:
                return inline_class.export_no_confirm(
                    request, inline_class.get_queryset(request)
                )
        return super().response_change(request, obj)
