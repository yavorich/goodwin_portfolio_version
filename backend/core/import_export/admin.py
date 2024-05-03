from django.http import HttpResponse
from import_export.admin import ExportMixin


class NoConfirmExportMixin(ExportMixin):
    def export_action(self, request):
        queryset = self.get_export_queryset(request)
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
