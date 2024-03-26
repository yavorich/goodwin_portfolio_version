from core.serializers.date_range import DateRangeSerializer


def get_dates_range(model, query_params):
    serializer = DateRangeSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)

    start_date = serializer.validated_data.get(
        "start_date", model.objects.earliest("created_at").created_at
    )
    end_date = serializer.validated_data.get(
        "end_date", model.objects.latest("created_at").created_at
    )

    return start_date, end_date
