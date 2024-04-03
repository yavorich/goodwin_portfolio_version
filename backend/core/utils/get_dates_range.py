from core.serializers.date_range import DateRangeSerializer
from django.db.models import Model


def get_dates_range(model: Model, query_params):
    serializer = DateRangeSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    start_date = serializer.validated_data.get(
        "start_date", getattr(model.objects.first(), "created_at", None)
    )
    end_date = serializer.validated_data.get(
        "end_date", getattr(model.objects.last(), "created_at", None)
    )

    return start_date, end_date
