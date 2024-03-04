from datetime import datetime, timedelta

from rest_framework.exceptions import ValidationError
from rest_framework.fields import DateField
from rest_framework.serializers import Serializer


class DateRangeSerializer(Serializer):
    start_date = DateField(required=False)
    end_date = DateField(required=False)

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date:
            delta = end_date - start_date
        elif start_date:
            delta = datetime.now().date() - start_date
        elif end_date:
            delta = end_date - datetime.now().date()
        else:
            return data

        if delta.days > 365 * 10:
            raise ValidationError("Разница между датами должна быть не больше 10 лет")
        return data
