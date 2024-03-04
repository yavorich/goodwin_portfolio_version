from rest_framework.serializers import FileField
from rest_framework.settings import api_settings


class HttpsFileField(FileField):
    def to_representation(self, value):
        if not value:
            return None

        use_url = getattr(self, "use_url", api_settings.UPLOADED_FILES_USE_URL)
        if use_url:
            try:
                url = value.url
            except AttributeError:
                return None
            request = self.context.get("request", None)
            if request is not None:
                return request.build_absolute_uri(url).replace("http", "https")
            return url

        return value.name
